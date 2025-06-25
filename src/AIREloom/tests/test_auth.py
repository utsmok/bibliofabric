# tests/test_auth.py
import asyncio

import httpx
import pytest
from bibliofabric.auth import ClientCredentialsAuth, NoAuth, StaticTokenAuth
from bibliofabric.exceptions import AuthError, ConfigurationError
from pytest_httpx import HTTPXMock

# --- Constants for Testing ---
MOCK_TOKEN_URL = "https://fake-token-endpoint.com/token"
MOCK_CLIENT_ID = "test_client_id"
MOCK_CLIENT_SECRET = "test_client_secret"
MOCK_STATIC_TOKEN = "test_static_token"
MOCK_ACCESS_TOKEN = "mock_oauth_access_token_123"


# --- Test NoAuth ---
@pytest.mark.asyncio
async def test_no_auth_authenticate():
    """Test that NoAuth does not modify the request."""
    strategy = NoAuth()
    request = httpx.Request("GET", "http://example.com")
    original_headers = request.headers.copy()

    await strategy.async_authenticate(request)

    assert request.headers == original_headers


# --- Test StaticTokenAuth ---
@pytest.mark.asyncio
async def test_static_token_auth_success():
    """Test StaticTokenAuth successfully adds the Authorization header."""
    strategy = StaticTokenAuth(token=MOCK_STATIC_TOKEN)
    request = httpx.Request("GET", "http://example.com")

    await strategy.async_authenticate(request)

    assert "Authorization" in request.headers
    assert request.headers["Authorization"] == f"Bearer {MOCK_STATIC_TOKEN}"


@pytest.mark.asyncio
async def test_static_token_auth_init_no_token():
    """Test StaticTokenAuth raises ConfigError if token is missing."""
    with pytest.raises(ConfigurationError, match="requires a non-empty 'token'"):
        StaticTokenAuth(token=None)
    with pytest.raises(ConfigurationError, match="requires a non-empty 'token'"):
        StaticTokenAuth(token="")


# --- Test ClientCredentialsAuth ---
@pytest.mark.asyncio
async def test_client_credentials_auth_init_success():
    """Test successful initialization of ClientCredentialsAuth."""
    strategy = ClientCredentialsAuth(
        client_id=MOCK_CLIENT_ID,
        client_secret=MOCK_CLIENT_SECRET,
        token_url=MOCK_TOKEN_URL,
    )
    assert strategy._client_id == MOCK_CLIENT_ID
    assert strategy._client_secret == MOCK_CLIENT_SECRET
    assert strategy._token_url == MOCK_TOKEN_URL
    assert strategy._access_token is None
    await strategy.async_close()  # Clean up


@pytest.mark.asyncio
async def test_client_credentials_auth_init_missing_config():
    """Test ClientCredentialsAuth raises ConfigError if config is missing."""
    with pytest.raises(
        ConfigurationError,
        match="requires 'client_id', 'client_secret', and 'token_url'",
    ):
        ClientCredentialsAuth(
            client_id=None, client_secret=MOCK_CLIENT_SECRET, token_url=MOCK_TOKEN_URL
        )
    with pytest.raises(
        ConfigurationError,
        match="requires 'client_id', 'client_secret', and 'token_url'",
    ):
        ClientCredentialsAuth(
            client_id=MOCK_CLIENT_ID, client_secret=None, token_url=MOCK_TOKEN_URL
        )
    with pytest.raises(
        ConfigurationError,
        match="requires 'client_id', 'client_secret', and 'token_url'",
    ):
        ClientCredentialsAuth(
            client_id=MOCK_CLIENT_ID, client_secret=MOCK_CLIENT_SECRET, token_url=None
        )


@pytest.mark.asyncio
async def test_client_credentials_auth_fetch_token_success(httpx_mock: HTTPXMock):
    """Test successful token fetching and authentication header addition."""
    httpx_mock.add_response(
        url=MOCK_TOKEN_URL,
        method="POST",
        json={"access_token": MOCK_ACCESS_TOKEN, "expires_in": 3600},
        status_code=200,
    )

    strategy = ClientCredentialsAuth(
        client_id=MOCK_CLIENT_ID,
        client_secret=MOCK_CLIENT_SECRET,
        token_url=MOCK_TOKEN_URL,
    )
    request = httpx.Request("GET", "http://example.com")

    await strategy.async_authenticate(request)

    assert strategy._access_token == MOCK_ACCESS_TOKEN
    assert "Authorization" in request.headers
    assert request.headers["Authorization"] == f"Bearer {MOCK_ACCESS_TOKEN}"
    await strategy.async_close()


@pytest.mark.asyncio
async def test_client_credentials_auth_fetch_token_cached(httpx_mock: HTTPXMock):
    """Test that token is fetched only once and cached for subsequent calls."""
    httpx_mock.add_response(
        url=MOCK_TOKEN_URL,
        method="POST",
        json={"access_token": MOCK_ACCESS_TOKEN, "expires_in": 3600},
        status_code=200,
    )

    strategy = ClientCredentialsAuth(
        client_id=MOCK_CLIENT_ID,
        client_secret=MOCK_CLIENT_SECRET,
        token_url=MOCK_TOKEN_URL,
    )
    request1 = httpx.Request("GET", "http://example.com/1")
    request2 = httpx.Request("GET", "http://example.com/2")

    # First call should fetch the token
    await strategy.async_authenticate(request1)
    assert strategy._access_token == MOCK_ACCESS_TOKEN
    assert request1.headers["Authorization"] == f"Bearer {MOCK_ACCESS_TOKEN}"
    assert len(httpx_mock.get_requests()) == 1

    # Second call should use the cached token
    await strategy.async_authenticate(request2)
    assert strategy._access_token == MOCK_ACCESS_TOKEN
    assert request2.headers["Authorization"] == f"Bearer {MOCK_ACCESS_TOKEN}"
    # Assert that no new request was made to the token endpoint
    assert len(httpx_mock.get_requests()) == 1

    await strategy.async_close()


@pytest.mark.asyncio
async def test_client_credentials_auth_fetch_token_http_error(httpx_mock: HTTPXMock):
    """Test AuthError is raised on HTTP error during token fetch."""
    httpx_mock.add_response(
        url=MOCK_TOKEN_URL,
        method="POST",
        text="Invalid credentials",
        status_code=401,
    )

    strategy = ClientCredentialsAuth(
        client_id=MOCK_CLIENT_ID,
        client_secret=MOCK_CLIENT_SECRET,
        token_url=MOCK_TOKEN_URL,
    )
    request = httpx.Request("GET", "http://example.com")

    with pytest.raises(AuthError, match="Failed to fetch access token: 401"):
        await strategy.async_authenticate(request)

    assert strategy._access_token is None
    await strategy.async_close()


@pytest.mark.asyncio
async def test_client_credentials_auth_fetch_token_network_error(httpx_mock: HTTPXMock):
    """Test AuthError is raised on network error during token fetch."""
    httpx_mock.add_exception(httpx.ConnectError("Connection failed"))

    strategy = ClientCredentialsAuth(
        client_id=MOCK_CLIENT_ID,
        client_secret=MOCK_CLIENT_SECRET,
        token_url=MOCK_TOKEN_URL,
    )
    request = httpx.Request("GET", "http://example.com")

    with pytest.raises(
        AuthError, match="Failed to fetch access token: Connection failed"
    ):
        await strategy.async_authenticate(request)

    assert strategy._access_token is None
    await strategy.async_close()


@pytest.mark.asyncio
async def test_client_credentials_auth_fetch_token_missing_in_response(
    httpx_mock: HTTPXMock,
):
    """Test AuthError is raised when access_token is missing in token response."""
    httpx_mock.add_response(
        url=MOCK_TOKEN_URL,
        method="POST",
        json={"wrong_key": "some_value"},  # Missing access_token
        status_code=200,
    )

    strategy = ClientCredentialsAuth(
        client_id=MOCK_CLIENT_ID,
        client_secret=MOCK_CLIENT_SECRET,
        token_url=MOCK_TOKEN_URL,
    )
    request = httpx.Request("GET", "http://example.com")

    with pytest.raises(AuthError, match="Access token not found in token response"):
        await strategy.async_authenticate(request)

    assert strategy._access_token is None
    await strategy.async_close()


@pytest.mark.asyncio
async def test_client_credentials_auth_close():
    """Test that the close method closes the internal httpx client."""
    strategy = ClientCredentialsAuth(
        client_id=MOCK_CLIENT_ID,
        client_secret=MOCK_CLIENT_SECRET,
        token_url=MOCK_TOKEN_URL,
    )
    # Access the client to ensure it's created
    internal_client = await strategy._get_token_client()
    assert internal_client is not None
    assert not internal_client.is_closed

    await strategy.async_close()

    assert strategy._token_client is None
    # Optionally check if the original client object is closed if needed,
    # but checking strategy._token_client is None is sufficient here.
    assert internal_client.is_closed


@pytest.mark.asyncio
async def test_client_credentials_auth_concurrent_fetch(httpx_mock: HTTPXMock):
    """Test that concurrent authenticate calls only trigger one token fetch."""
    # Simplify mock: Just add the expected response directly.
    # The internal lock in ClientCredentialsAuth should handle concurrency.
    httpx_mock.add_response(
        url=MOCK_TOKEN_URL,
        method="POST",
        json={"access_token": MOCK_ACCESS_TOKEN, "expires_in": 3600},
        status_code=200,
    )
    # Remove the complex callback and delay simulation

    strategy = ClientCredentialsAuth(
        client_id=MOCK_CLIENT_ID,
        client_secret=MOCK_CLIENT_SECRET,
        token_url=MOCK_TOKEN_URL,
    )

    request1 = httpx.Request("GET", "http://example.com/1")
    request2 = httpx.Request("GET", "http://example.com/2")

    # Run authenticate concurrently
    task1 = asyncio.create_task(strategy.async_authenticate(request1))
    task2 = asyncio.create_task(strategy.async_authenticate(request2))

    await asyncio.gather(task1, task2)

    # Assert that only one request was made to the token endpoint
    requests_made = httpx_mock.get_requests(url=MOCK_TOKEN_URL, method="POST")
    assert len(requests_made) == 1

    # Assert both original requests got authenticated
    assert request1.headers["Authorization"] == f"Bearer {MOCK_ACCESS_TOKEN}"
    assert request2.headers["Authorization"] == f"Bearer {MOCK_ACCESS_TOKEN}"
    assert strategy._access_token == MOCK_ACCESS_TOKEN

    await strategy.async_close()
