"""Authentication strategies for bibliofabric-family clients.

A strategy mutates the outgoing ``httpx.Request`` in place (header or query
parameter) and may hold resources closable through ``async_close()`` /
``close()``. Strategies are shared by both client variants: one object works
with an async client (``async_authenticate``) and a sync client
(``authenticate``), so every strategy implements both method pairs.
"""

import asyncio
import logging
import threading
import time
from typing import Protocol

import httpx

from .exceptions import AuthError, ConfigurationError

logger = logging.getLogger(__name__)


class AuthStrategy(Protocol):
    """Applies credentials to an outgoing request, for both client variants."""

    async def async_authenticate(self, request: httpx.Request) -> None:
        """Modify ``request`` to carry authentication information."""
        ...

    async def async_close(self) -> None:
        """Release underlying resources; must be idempotent."""
        ...

    def authenticate(self, request: httpx.Request) -> None:
        """Sync twin of :meth:`async_authenticate`."""
        ...

    def close(self) -> None:
        """Sync twin of :meth:`async_close`; must be idempotent."""
        ...


class NoAuth:
    """Strategy for APIs that need no authentication."""

    async def async_authenticate(self, request: httpx.Request) -> None:
        """Do nothing."""

    async def async_close(self) -> None:
        """Nothing to close."""

    def authenticate(self, request: httpx.Request) -> None:
        """Do nothing."""

    def close(self) -> None:
        """Nothing to close."""


class StaticTokenAuth:
    """Adds ``Authorization: Bearer <token>`` to every request."""

    def __init__(self, token: str) -> None:
        if not token:
            raise ConfigurationError("StaticTokenAuth requires a non-empty 'token'.")
        self._token = token

    async def async_authenticate(self, request: httpx.Request) -> None:
        request.headers["Authorization"] = f"Bearer {self._token}"

    async def async_close(self) -> None:
        """Nothing to close."""

    def authenticate(self, request: httpx.Request) -> None:
        request.headers["Authorization"] = f"Bearer {self._token}"

    def close(self) -> None:
        """Nothing to close."""


class QueryParameterAuth:
    """Adds the credential as a URL query parameter (e.g. OpenAlex ``api_key``)."""

    def __init__(self, key_name: str, key_value: str) -> None:
        if not key_name or not key_value:
            raise ConfigurationError(
                "QueryParameterAuth requires a non-empty 'key_name' and 'key_value'."
            )
        self._key_name = key_name
        self._key_value = key_value

    async def async_authenticate(self, request: httpx.Request) -> None:
        request.url = request.url.copy_merge_params({self._key_name: self._key_value})

    async def async_close(self) -> None:
        """Nothing to close."""

    def authenticate(self, request: httpx.Request) -> None:
        request.url = request.url.copy_merge_params({self._key_name: self._key_value})

    def close(self) -> None:
        """Nothing to close."""


class HeaderAuth:
    """Adds a static credential under a named header (e.g. Crossref Plus)."""

    def __init__(self, name: str, value: str) -> None:
        if not name or not value:
            raise ConfigurationError(
                "HeaderAuth requires a non-empty 'name' and 'value'."
            )
        self._name = name
        self._value = value

    async def async_authenticate(self, request: httpx.Request) -> None:
        request.headers[self._name] = self._value

    async def async_close(self) -> None:
        """Nothing to close."""

    def authenticate(self, request: httpx.Request) -> None:
        request.headers[self._name] = self._value

    def close(self) -> None:
        """Nothing to close."""


class ClientCredentialsAuth:
    """OAuth2 client-credentials flow with an in-memory token cache.

    Fetches a bearer token from ``token_url`` using ``client_id`` and
    ``client_secret`` and reuses it until shortly before ``expires_in``. The
    cached token is shared by both client variants; each variant lazily
    creates its own ``httpx`` client for the token request and serializes its
    refreshes behind its own lock (``asyncio.Lock`` for the async twin,
    ``threading.Lock`` for the sync twin). Pass ``user_agent`` so the token
    clients identify themselves like the main client does.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_url: str,
        *,
        user_agent: str | None = None,
    ) -> None:
        missing = [
            name
            for name, value in (
                ("client_id", client_id),
                ("client_secret", client_secret),
                ("token_url", token_url),
            )
            if not value
        ]
        if missing:
            raise ConfigurationError(
                f"ClientCredentialsAuth requires non-empty: {', '.join(missing)}."
            )
        self._client_id = client_id
        self._client_secret = client_secret
        self._token_url = token_url
        self._user_agent = user_agent
        self._access_token: str | None = None
        self._token_expires_at: float | None = None
        self._async_token_client: httpx.AsyncClient | None = None
        self._sync_token_client: httpx.Client | None = None
        self._async_lock: asyncio.Lock | None = None
        self._sync_lock = threading.Lock()

    def _get_async_client(self) -> httpx.AsyncClient:
        if self._async_token_client is None:
            headers = {"User-Agent": self._user_agent} if self._user_agent else None
            self._async_token_client = httpx.AsyncClient(timeout=15.0, headers=headers)
        return self._async_token_client

    def _get_sync_client(self) -> httpx.Client:
        if self._sync_token_client is None:
            headers = {"User-Agent": self._user_agent} if self._user_agent else None
            self._sync_token_client = httpx.Client(timeout=15.0, headers=headers)
        return self._sync_token_client

    def _is_token_expired(self) -> bool:
        if self._access_token is None:
            return True
        if self._token_expires_at is None:
            return False
        return time.time() >= self._token_expires_at

    def _store_token(self, payload: object) -> str:
        """Validate a token-endpoint payload and cache the new token."""
        if not isinstance(payload, dict):
            raise AuthError("Token endpoint returned a non-object payload.")
        access_token = payload.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise AuthError("Token response did not contain an 'access_token'.")

        expires_in = payload.get("expires_in")
        try:
            self._token_expires_at = (
                time.time() + float(expires_in) - 30 if expires_in else None
            )
        except (TypeError, ValueError):
            self._token_expires_at = None
        self._access_token = access_token
        logger.debug("Successfully fetched new access token.")
        return access_token

    async def _fetch_access_token(self) -> str:
        if self._async_lock is None:
            self._async_lock = asyncio.Lock()
        async with self._async_lock:
            if self._access_token is not None and not self._is_token_expired():
                return self._access_token

            logger.debug("Fetching new access token from %s", self._token_url)
            try:
                response = await self._get_async_client().post(
                    self._token_url,
                    auth=httpx.BasicAuth(
                        username=self._client_id, password=self._client_secret
                    ),
                    data={"grant_type": "client_credentials"},
                )
                response.raise_for_status()
            except Exception as error:
                raise AuthError(f"Failed to fetch access token: {error}") from error
            return self._store_token(response.json())

    def _fetch_access_token_sync(self) -> str:
        with self._sync_lock:
            if self._access_token is not None and not self._is_token_expired():
                return self._access_token

            logger.debug("Fetching new access token from %s", self._token_url)
            try:
                response = self._get_sync_client().post(
                    self._token_url,
                    auth=httpx.BasicAuth(
                        username=self._client_id, password=self._client_secret
                    ),
                    data={"grant_type": "client_credentials"},
                )
                response.raise_for_status()
            except Exception as error:
                raise AuthError(f"Failed to fetch access token: {error}") from error
            return self._store_token(response.json())

    async def async_authenticate(self, request: httpx.Request) -> None:
        if self._access_token is None or self._is_token_expired():
            await self._fetch_access_token()
        request.headers["Authorization"] = f"Bearer {self._access_token}"

    async def async_close(self) -> None:
        if self._async_token_client is not None:
            await self._async_token_client.aclose()
            self._async_token_client = None

    def authenticate(self, request: httpx.Request) -> None:
        if self._access_token is None or self._is_token_expired():
            self._fetch_access_token_sync()
        request.headers["Authorization"] = f"Bearer {self._access_token}"

    def close(self) -> None:
        if self._sync_token_client is not None:
            self._sync_token_client.close()
            self._sync_token_client = None
