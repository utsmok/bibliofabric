"""Authentication strategies for bibliofabric-family clients.

A strategy mutates the outgoing ``httpx.Request`` in place (header or query
parameter) and may hold resources closable through ``async_close()`` /
``close()``. Strategies are shared by both client variants: one object works
with an async client (``async_authenticate``) and a sync client
(``authenticate``), so every strategy implements both method pairs.
"""

import asyncio
import base64
import logging
import math
import threading
import time
from typing import Any, Literal, Protocol

import httpx

from .exceptions import AuthError, ConfigurationError
from .utils import sanitize_url

logger = logging.getLogger(__name__)

_TOKEN_REFRESH_BUFFER_SECONDS = 30.0
TokenAuthMethod = Literal["basic", "post"]
_VALID_TOKEN_AUTH_METHODS = frozenset({"basic", "post"})


def _safe_json_body(response: httpx.Response) -> Any:
    try:
        return response.json()
    except Exception:
        return None


def _validate_timeout(timeout: float, owner: str) -> None:
    if not math.isfinite(timeout) or timeout <= 0:
        raise ConfigurationError(
            f"{owner} requires a positive finite 'timeout', got {timeout!r}."
        )


class AuthStrategy(Protocol):
    """Applies credentials to an outgoing request, for both client variants.

    Strategies may optionally expose ``redacted_query_params`` and
    ``redacted_headers`` (``frozenset[str]``) naming custom query parameters
    or headers whose values should be scrubbed from logs and error messages;
    when omitted, both default to empty sets. Token-caching strategies may
    also expose ``invalidate_token() -> None`` so ``BaseApiClient`` can
    refresh the token and retry once on HTTP 401.
    """

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

    redacted_query_params: frozenset[str] = frozenset()
    redacted_headers: frozenset[str] = frozenset()

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

    redacted_query_params: frozenset[str] = frozenset()
    redacted_headers: frozenset[str] = frozenset({"authorization"})

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


class BasicAuth:
    """Adds HTTP Basic authentication (``Authorization: Basic <base64>``)."""

    redacted_query_params: frozenset[str] = frozenset()
    redacted_headers: frozenset[str] = frozenset({"authorization"})

    def __init__(self, username: str, password: str) -> None:
        if not username or not password:
            raise ConfigurationError(
                "BasicAuth requires a non-empty 'username' and 'password'."
            )
        encoded = base64.b64encode(f"{username}:{password}".encode()).decode("ascii")
        self._header_value = f"Basic {encoded}"

    async def async_authenticate(self, request: httpx.Request) -> None:
        request.headers["Authorization"] = self._header_value

    async def async_close(self) -> None:
        """Nothing to close."""

    def authenticate(self, request: httpx.Request) -> None:
        request.headers["Authorization"] = self._header_value

    def close(self) -> None:
        """Nothing to close."""


class QueryParameterAuth:
    """Adds the credential as a URL query parameter (e.g. OpenAlex ``api_key``)."""

    redacted_headers: frozenset[str] = frozenset()

    def __init__(self, key_name: str, key_value: str) -> None:
        if not key_name or not key_value:
            raise ConfigurationError(
                "QueryParameterAuth requires a non-empty 'key_name' and 'key_value'."
            )
        self._key_name = key_name
        self._key_value = key_value
        self.redacted_query_params: frozenset[str] = frozenset({key_name})

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

    redacted_query_params: frozenset[str] = frozenset()

    def __init__(self, name: str, value: str) -> None:
        if not name or not value:
            raise ConfigurationError(
                "HeaderAuth requires a non-empty 'name' and 'value'."
            )
        self._name = name
        self._value = value
        self.redacted_headers: frozenset[str] = frozenset({name.lower()})

    async def async_authenticate(self, request: httpx.Request) -> None:
        request.headers[self._name] = self._value

    async def async_close(self) -> None:
        """Nothing to close."""

    def authenticate(self, request: httpx.Request) -> None:
        request.headers[self._name] = self._value

    def close(self) -> None:
        """Nothing to close."""


class _OAuth2TokenAuth:
    """Shared in-memory token caching and HTTP lifecycle for OAuth2 flows."""

    redacted_query_params: frozenset[str] = frozenset()
    redacted_headers: frozenset[str] = frozenset({"authorization"})

    def __init__(
        self,
        *,
        token_url: str,
        user_agent: str | None = None,
        timeout: float = 30.0,
        http_client: httpx.AsyncClient | httpx.Client | None = None,
    ) -> None:
        _validate_timeout(timeout, type(self).__name__)
        self._token_url = token_url
        self._user_agent = user_agent
        self._timeout = timeout
        self._access_token: str | None = None
        self._token_expires_at: float | None = None
        self._async_token_client: httpx.AsyncClient | None = (
            http_client if isinstance(http_client, httpx.AsyncClient) else None
        )
        self._owns_async_client = self._async_token_client is None
        self._sync_token_client: httpx.Client | None = (
            http_client if isinstance(http_client, httpx.Client) else None
        )
        self._owns_sync_client = self._sync_token_client is None
        self._async_lock: asyncio.Lock | None = None
        self._sync_lock = threading.Lock()

    def invalidate_token(self) -> None:
        """Drop any cached access token so the next request fetches a fresh one."""
        self._access_token = None
        self._token_expires_at = None

    def _get_async_client(self) -> httpx.AsyncClient:
        if self._async_token_client is None:
            headers = {"User-Agent": self._user_agent} if self._user_agent else None
            self._async_token_client = httpx.AsyncClient(
                timeout=self._timeout, headers=headers
            )
            self._owns_async_client = True
        return self._async_token_client

    def _get_sync_client(self) -> httpx.Client:
        if self._sync_token_client is None:
            headers = {"User-Agent": self._user_agent} if self._user_agent else None
            self._sync_token_client = httpx.Client(
                timeout=self._timeout, headers=headers
            )
            self._owns_sync_client = True
        return self._sync_token_client

    def _is_token_expired(self) -> bool:
        if self._access_token is None:
            return True
        if self._token_expires_at is None:
            return False
        return time.monotonic() >= self._token_expires_at

    def _token_request_payload(self) -> tuple[httpx.Auth | None, dict[str, str]]:
        raise NotImplementedError

    def _store_token(
        self, payload: object, *, response: httpx.Response | None = None
    ) -> str:
        """Validate a token-endpoint payload and cache the new token."""
        if not isinstance(payload, dict):
            raise AuthError(
                "Token endpoint returned a non-object payload.",
                body=payload,
                response=response,
            )
        access_token = payload.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise AuthError(
                "Token response did not contain an 'access_token'.",
                body=payload,
                response=response,
            )

        expires_in = payload.get("expires_in")
        if expires_in is None:
            self._token_expires_at = None
        else:
            try:
                seconds = float(expires_in)
            except (TypeError, ValueError):
                self._token_expires_at = None
            else:
                if not math.isfinite(seconds):
                    self._token_expires_at = None
                elif seconds <= 0:
                    self._token_expires_at = time.monotonic()
                else:
                    buffer = min(_TOKEN_REFRESH_BUFFER_SECONDS, seconds * 0.5)
                    self._token_expires_at = time.monotonic() + seconds - buffer
        self._access_token = access_token
        logger.debug("Successfully fetched new access token.")
        return access_token

    def _parse_token_response(self, response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError as error:
            raise AuthError(
                f"Token endpoint returned invalid JSON: {error}",
                response=response,
            ) from error
        return self._store_token(payload, response=response)

    async def _fetch_access_token(self) -> str:
        if self._async_lock is None:
            self._async_lock = asyncio.Lock()
        async with self._async_lock:
            if self._access_token is not None and not self._is_token_expired():
                return self._access_token

            logger.debug(
                "Fetching new access token from %s", sanitize_url(self._token_url)
            )
            auth, data = self._token_request_payload()
            try:
                response = await self._get_async_client().post(
                    self._token_url,
                    auth=auth if auth is not None else httpx.USE_CLIENT_DEFAULT,
                    data=data,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as error:
                raise AuthError(
                    f"Failed to fetch access token: {sanitize_url(str(error))}",
                    body=_safe_json_body(error.response),
                    request=error.request,
                    response=error.response,
                ) from error
            except httpx.HTTPError as error:
                raise AuthError(
                    f"Failed to fetch access token: {sanitize_url(str(error))}",
                    request=getattr(error, "request", None),
                ) from error
            except Exception as error:
                raise AuthError(
                    f"Failed to fetch access token: {sanitize_url(str(error))}"
                ) from error
            return self._parse_token_response(response)

    def _fetch_access_token_sync(self) -> str:
        with self._sync_lock:
            if self._access_token is not None and not self._is_token_expired():
                return self._access_token

            logger.debug(
                "Fetching new access token from %s", sanitize_url(self._token_url)
            )
            auth, data = self._token_request_payload()
            try:
                response = self._get_sync_client().post(
                    self._token_url,
                    auth=auth if auth is not None else httpx.USE_CLIENT_DEFAULT,
                    data=data,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as error:
                raise AuthError(
                    f"Failed to fetch access token: {sanitize_url(str(error))}",
                    body=_safe_json_body(error.response),
                    request=error.request,
                    response=error.response,
                ) from error
            except httpx.HTTPError as error:
                raise AuthError(
                    f"Failed to fetch access token: {sanitize_url(str(error))}",
                    request=getattr(error, "request", None),
                ) from error
            except Exception as error:
                raise AuthError(
                    f"Failed to fetch access token: {sanitize_url(str(error))}"
                ) from error
            return self._parse_token_response(response)

    async def async_authenticate(self, request: httpx.Request) -> None:
        token = self._access_token
        if token is None or self._is_token_expired():
            token = await self._fetch_access_token()
        request.headers["Authorization"] = f"Bearer {token}"

    async def async_close(self) -> None:
        if self._async_token_client is not None and self._owns_async_client:
            await self._async_token_client.aclose()
            self._async_token_client = None

    def authenticate(self, request: httpx.Request) -> None:
        token = self._access_token
        if token is None or self._is_token_expired():
            token = self._fetch_access_token_sync()
        request.headers["Authorization"] = f"Bearer {token}"

    def close(self) -> None:
        if self._sync_token_client is not None and self._owns_sync_client:
            self._sync_token_client.close()
            self._sync_token_client = None


class ClientCredentialsAuth(_OAuth2TokenAuth):
    """OAuth2 client-credentials flow with an in-memory token cache.

    Fetches a bearer token from ``token_url`` using ``client_id`` and
    ``client_secret`` and reuses it until shortly before ``expires_in``. The
    cached token is shared by both client variants; each variant lazily
    creates its own ``httpx`` client for the token request (unless an external
    ``http_client`` is provided) and serializes its refreshes behind its own
    lock (``asyncio.Lock`` for the async twin, ``threading.Lock`` for the sync
    twin). Set ``token_auth_method="post"`` for token endpoints (such as
    ORCID) that expect ``client_id`` and ``client_secret`` in the form body
    rather than an HTTP Basic header.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_url: str,
        *,
        scope: str | None = None,
        token_auth_method: TokenAuthMethod = "basic",
        user_agent: str | None = None,
        timeout: float = 30.0,
        http_client: httpx.AsyncClient | httpx.Client | None = None,
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
        if token_auth_method not in _VALID_TOKEN_AUTH_METHODS:
            raise ConfigurationError(
                "ClientCredentialsAuth token_auth_method must be 'basic' or 'post', "
                f"got {token_auth_method!r}."
            )
        super().__init__(
            token_url=token_url,
            user_agent=user_agent,
            timeout=timeout,
            http_client=http_client,
        )
        self._client_id = client_id
        self._client_secret = client_secret
        self._scope = scope
        self._token_auth_method = token_auth_method

    def _token_request_payload(self) -> tuple[httpx.Auth | None, dict[str, str]]:
        data: dict[str, str] = {"grant_type": "client_credentials"}
        if self._scope:
            data["scope"] = self._scope
        if self._token_auth_method == "post":
            data["client_id"] = self._client_id
            data["client_secret"] = self._client_secret
            return None, data
        return (
            httpx.BasicAuth(username=self._client_id, password=self._client_secret),
            data,
        )


class RefreshTokenAuth(_OAuth2TokenAuth):
    """OAuth2 refresh-token flow with an in-memory access-token cache.

    Exchanges ``refresh_token`` at ``token_url`` for a bearer access token,
    caches it with ``time.monotonic()`` until shortly before ``expires_in``,
    and updates the stored refresh token when the server rotates it.
    """

    def __init__(
        self,
        token_url: str,
        refresh_token: str,
        *,
        client_id: str | None = None,
        client_secret: str | None = None,
        scope: str | None = None,
        user_agent: str | None = None,
        timeout: float = 30.0,
        http_client: httpx.AsyncClient | httpx.Client | None = None,
    ) -> None:
        missing = [
            name
            for name, value in (
                ("token_url", token_url),
                ("refresh_token", refresh_token),
            )
            if not value
        ]
        if missing:
            raise ConfigurationError(
                f"RefreshTokenAuth requires non-empty: {', '.join(missing)}."
            )
        if client_id is not None and not client_id:
            raise ConfigurationError(
                "RefreshTokenAuth 'client_id' must be non-empty when provided."
            )
        if client_secret is not None and not client_secret:
            raise ConfigurationError(
                "RefreshTokenAuth 'client_secret' must be non-empty when provided."
            )
        super().__init__(
            token_url=token_url,
            user_agent=user_agent,
            timeout=timeout,
            http_client=http_client,
        )
        self._refresh_token = refresh_token
        self._client_id = client_id
        self._client_secret = client_secret
        self._scope = scope

    def _token_request_payload(self) -> tuple[httpx.Auth | None, dict[str, str]]:
        data: dict[str, str] = {
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
        }
        if self._client_id is not None:
            data["client_id"] = self._client_id
        if self._client_secret is not None:
            data["client_secret"] = self._client_secret
        if self._scope:
            data["scope"] = self._scope
        return None, data

    def _store_token(
        self, payload: object, *, response: httpx.Response | None = None
    ) -> str:
        access_token = super()._store_token(payload, response=response)
        if isinstance(payload, dict):
            rotated = payload.get("refresh_token")
            if isinstance(rotated, str) and rotated:
                self._refresh_token = rotated
        return access_token


__all__ = [
    "AuthStrategy",
    "BasicAuth",
    "ClientCredentialsAuth",
    "HeaderAuth",
    "NoAuth",
    "QueryParameterAuth",
    "RefreshTokenAuth",
    "StaticTokenAuth",
    "TokenAuthMethod",
]
