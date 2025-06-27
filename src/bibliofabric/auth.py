import asyncio
from enum import Enum
from typing import Protocol

import httpx

from .exceptions import AuthError, ConfigurationError
from .log_config import logger


class AuthStrategyType(Enum):
    """Enumeration of available authentication strategy types.

    Used in configuration to specify which authentication method to use.
    """

    NONE = "none"
    STATIC_TOKEN = "static_token"
    CLIENT_CREDENTIALS = "client_credentials"


class AuthStrategy(Protocol):
    """Protocol defining the interface for various authentication strategies.

    Concrete implementations of this protocol handle the specifics of adding
    authentication information (e.g., headers, tokens) to an HTTP request.
    """

    async def async_authenticate(self, request: httpx.Request) -> None:
        """
        Asynchronously modifies the request to add authentication information.

        Args:
            request: The httpx.Request object to modify.

        Raises:
            AuthError: If authentication fails (e.g., token fetching).
            ConfigurationError: If required configuration for the strategy is missing.
        """
        ...

    async def async_close(self) -> None:
        """
        Asynchronously closes any underlying resources used by the auth strategy,
        if applicable (e.g., an HTTP client for token fetching).
        This method should be idempotent.
        """
        ...


class NoAuth:
    """Implements the AuthStrategy protocol for requests requiring no authentication.

    This strategy makes no modifications to the outgoing request.
    """

    async def async_authenticate(self, request: httpx.Request) -> None:
        """Does nothing as no authentication is needed."""
        logger.trace("Using NoAuth strategy, no authentication applied.")

    async def async_close(self) -> None:
        """No resources to close for NoAuth, this method is a no-op."""


class StaticTokenAuth:
    """Implements AuthStrategy using a static Bearer token.

    This strategy is suitable for APIs that use a pre-issued, long-lived
    API token (e.g., a personal access token). The token is added to the
    `Authorization` header as a Bearer token.

    Attributes:
        _token: The static API token.
    """

    def __init__(self, token: str | None):
        """Initializes StaticTokenAuth with the provided API token.

        Args:
            token: The static API token to use for authentication.

        Raises:
            ConfigurationError: If the token is None or empty.
        """
        if not token:
            raise ConfigurationError("StaticTokenAuth requires a non-empty 'token'.")
        self._token: str = token
        logger.debug("StaticTokenAuth initialized.")

    async def async_authenticate(self, request: httpx.Request) -> None:
        """Adds the static 'Authorization: Bearer <token>' header to the request."""
        logger.trace("Authenticating request using StaticTokenAuth.")
        request.headers["Authorization"] = f"Bearer {self._token}"

    async def async_close(self) -> None:
        """No resources to close for StaticTokenAuth, this method is a no-op."""


class ClientCredentialsAuth:
    """Implements AuthStrategy using OAuth2 Client Credentials Grant Flow.

    This strategy fetches a Bearer token from a specified token URL using
    client ID and client secret, then uses this token for subsequent API requests.
    It handles token fetching and includes a lock to prevent concurrent token requests.

    Attributes:
        _client_id: The OAuth2 client ID.
        _client_secret: The OAuth2 client secret.
        _token_url: The URL of the OAuth2 token endpoint.
        _access_token: The currently active access token.
        _token_client: An internal httpx.AsyncClient for fetching the token.
        _fetch_lock: An asyncio.Lock to prevent race conditions during token fetching.
    """

    def __init__(
        self, client_id: str | None, client_secret: str | None, token_url: str | None
    ):
        if not all([client_id, client_secret, token_url]):
            raise ConfigurationError(
                "ClientCredentialsAuth requires 'client_id', 'client_secret', and 'token_url'."
            )
        assert client_id is not None, "client_id cannot be None here"
        assert client_secret is not None, "client_secret cannot be None here"
        assert token_url is not None, "token_url cannot be None here"
        self._client_id: str = client_id
        self._client_secret: str = client_secret
        self._token_url: str = token_url
        self._access_token: str | None = None
        self._token_client: httpx.AsyncClient | None = None
        self._fetch_lock = asyncio.Lock()
        logger.debug("ClientCredentialsAuth initialized.")

    async def _get_token_client(self) -> httpx.AsyncClient:
        """Lazily initializes and returns an internal httpx.AsyncClient for token requests.

        Returns:
            An httpx.AsyncClient instance.
        """
        if self._token_client is None:
            self._token_client = httpx.AsyncClient(
                timeout=15.0
            )  # Standard timeout for token requests
        return self._token_client

    async def _fetch_access_token(self) -> str:
        """Fetches a new OAuth2 access token using the client credentials grant type.

        This method handles the POST request to the token URL and extracts the
        access token from the JSON response. It uses a lock to prevent multiple
        concurrent requests for a new token.

        Returns:
            The fetched access token as a string.

        Raises:
            AuthError: If token fetching fails due to HTTP errors, network issues,
                       or an invalid response from the token endpoint.
        """
        async with self._fetch_lock:
            # Double-check if token was fetched while waiting for the lock
            if self._access_token:
                return self._access_token

            logger.info(f"Fetching new access token from {self._token_url}")
            client = await self._get_token_client()
            try:
                response = await client.post(
                    url=self._token_url,
                    auth=httpx.BasicAuth(
                        username=self._client_id, password=self._client_secret
                    ),
                    data={"grant_type": "client_credentials"},
                )
                response.raise_for_status()  # Raise HTTPStatusError for bad responses (4xx or 5xx)
                token_data = response.json()
                access_token = token_data.get("access_token")
                if not access_token:
                    raise AuthError("Access token not found in token response.")
                # TODO: Handle token expiry ('expires_in') for future automatic refresh
                # expires_in = token_data.get("expires_in")
                logger.info("Successfully fetched new access token.")
                self._access_token = access_token
                assert self._access_token is not None, "Access token should be set here"
                return self._access_token
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"HTTP error fetching token: {e.response.status_code} - {e.response.text}"
                )
                raise AuthError(
                    f"Failed to fetch access token: {e.response.status_code} - {e.response.text}"
                ) from e
            except (httpx.RequestError, Exception) as e:
                logger.error(f"Error fetching token: {e}")
                raise AuthError(f"Failed to fetch access token: {e}") from e

    async def async_authenticate(self, request: httpx.Request) -> None:
        """Ensures a valid token is fetched and adds the Authorization header."""
        logger.trace("Authenticating request using ClientCredentialsAuth.")
        if not self._access_token:
            # Fetch token if not already available (first time or after expiry if implemented)
            await self._fetch_access_token()

        if not self._access_token:
            # Should not happen if fetch was successful, but check anyway
            raise AuthError("Authentication failed: Could not obtain access token.")

        request.headers["Authorization"] = f"Bearer {self._access_token}"

    async def async_close(self) -> None:
        """Closes the internal HTTP client used for token fetching."""
        if self._token_client:
            await self._token_client.aclose()
            self._token_client = None
            logger.debug("ClientCredentialsAuth internal client closed.")
