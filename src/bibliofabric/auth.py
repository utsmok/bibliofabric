"""Authentication strategies for bibliofabric-family clients.

A strategy mutates the outgoing ``httpx.Request`` in place (header or query
parameter) and may hold resources closable through ``async_close()``.
"""

import asyncio
import logging
import time
from typing import Protocol

import httpx

from .exceptions import AuthError, ConfigurationError

logger = logging.getLogger(__name__)


class AuthStrategy(Protocol):
    """Applies credentials to an outgoing request."""

    async def async_authenticate(self, request: httpx.Request) -> None:
        """Modify ``request`` to carry authentication information."""
        ...

    async def async_close(self) -> None:
        """Release underlying resources; must be idempotent."""
        ...


class NoAuth:
    """Strategy for APIs that need no authentication."""

    async def async_authenticate(self, request: httpx.Request) -> None:
        """Do nothing."""

    async def async_close(self) -> None:
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


class ClientCredentialsAuth:
    """OAuth2 client-credentials flow with in-memory token caching.

    Fetches a bearer token from ``token_url`` using ``client_id`` and
    ``client_secret``, reuses it until shortly before ``expires_in``, and
    serializes concurrent fetches behind a lock. Pass ``user_agent`` so the
    token client identifies itself like the main client does.
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
        self._token_client: httpx.AsyncClient | None = None
        self._fetch_lock = asyncio.Lock()

    def _get_token_client(self) -> httpx.AsyncClient:
        if self._token_client is None:
            headers = {"User-Agent": self._user_agent} if self._user_agent else None
            self._token_client = httpx.AsyncClient(timeout=15.0, headers=headers)
        return self._token_client

    def _is_token_expired(self) -> bool:
        if self._access_token is None:
            return True
        if self._token_expires_at is None:
            return False
        return time.time() >= self._token_expires_at

    async def _fetch_access_token(self) -> str:
        async with self._fetch_lock:
            if self._access_token is not None and not self._is_token_expired():
                return self._access_token

            logger.debug("Fetching new access token from %s", self._token_url)
            client = self._get_token_client()
            try:
                response = await client.post(
                    self._token_url,
                    auth=httpx.BasicAuth(
                        username=self._client_id, password=self._client_secret
                    ),
                    data={"grant_type": "client_credentials"},
                )
                response.raise_for_status()
                payload = response.json()
            except Exception as error:
                raise AuthError(f"Failed to fetch access token: {error}") from error

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

    async def async_authenticate(self, request: httpx.Request) -> None:
        if self._access_token is None or self._is_token_expired():
            await self._fetch_access_token()
        request.headers["Authorization"] = f"Bearer {self._access_token}"

    async def async_close(self) -> None:
        if self._token_client is not None:
            await self._token_client.aclose()
            self._token_client = None
