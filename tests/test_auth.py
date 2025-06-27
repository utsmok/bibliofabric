"""Tests for the authentication strategies in bibliofabric."""

from unittest.mock import patch

import httpx
import pytest

from bibliofabric.auth import ClientCredentialsAuth, NoAuth, StaticTokenAuth
from bibliofabric.exceptions import AuthError, ConfigurationError


@pytest.mark.asyncio
async def test_no_auth_authenticate():
    """Test NoAuth strategy does not modify the request."""
    request = httpx.Request("GET", "http://example.com")
    original_headers = dict(request.headers)
    await NoAuth().async_authenticate(request)
    assert dict(request.headers) == original_headers


@pytest.mark.asyncio
async def test_no_auth_close():
    """Test NoAuth strategy close method does nothing."""
    await NoAuth().async_close()
    # No exception means it passed


def test_static_token_auth_init_success():
    """Test StaticTokenAuth initializes successfully with a token."""
    auth = StaticTokenAuth(token="test_token")
    assert auth._token == "test_token"


def test_static_token_auth_init_no_token():
    """Test StaticTokenAuth raises ConfigurationError if no token is provided."""
    with pytest.raises(
        ConfigurationError, match="StaticTokenAuth requires a non-empty 'token'."
    ):
        StaticTokenAuth(token="")
    with pytest.raises(
        ConfigurationError, match="StaticTokenAuth requires a non-empty 'token'."
    ):
        StaticTokenAuth(token=None)


@pytest.mark.asyncio
async def test_static_token_auth_authenticate():
    """Test StaticTokenAuth adds the Authorization header."""
    auth = StaticTokenAuth(token="test_token")
    request = httpx.Request("GET", "http://example.com")
    await auth.async_authenticate(request)
    assert request.headers["Authorization"] == "Bearer test_token"


@pytest.mark.asyncio
async def test_static_token_auth_close():
    """Test StaticTokenAuth close method does nothing."""
    auth = StaticTokenAuth(token="test_token")
    await auth.async_close()
    # No exception means it passed


def test_client_credentials_auth_init_success():
    """Test ClientCredentialsAuth initializes successfully."""
    auth = ClientCredentialsAuth(
        client_id="id", client_secret="secret", token_url="http://token.com"
    )
    assert auth._client_id == "id"
    assert auth._client_secret == "secret"
    assert auth._token_url == "http://token.com"
    assert auth._access_token is None
    assert auth._token_client is None


def test_client_credentials_auth_init_missing_params():
    """Test ClientCredentialsAuth raises ConfigurationError for missing parameters."""
    with pytest.raises(
        ConfigurationError,
        match="ClientCredentialsAuth requires 'client_id', 'client_secret', and 'token_url'.",
    ):
        ClientCredentialsAuth(
            client_id=None, client_secret="secret", token_url="http://token.com"
        )
    with pytest.raises(
        ConfigurationError,
        match="ClientCredentialsAuth requires 'client_id', 'client_secret', and 'token_url'.",
    ):
        ClientCredentialsAuth(
            client_id="id", client_secret=None, token_url="http://token.com"
        )
    with pytest.raises(
        ConfigurationError,
        match="ClientCredentialsAuth requires 'client_id', 'client_secret', and 'token_url'.",
    ):
        ClientCredentialsAuth(client_id="id", client_secret="secret", token_url=None)


@pytest.mark.asyncio
@patch("httpx.BasicAuth")
@patch("httpx.AsyncClient.post")
async def test_client_credentials_auth_fetch_token_success(mock_post, MockBasicAuth):
    """Test ClientCredentialsAuth successfully fetches an access token."""
    mock_post.return_value = httpx.Response(
        200,
        json={"access_token": "new_token", "expires_in": 3600},
        request=httpx.Request("POST", "http://token.com"),
    )

    auth = ClientCredentialsAuth(
        client_id="id", client_secret="secret", token_url="http://token.com"
    )
    token = await auth._fetch_access_token()

    assert token == "new_token"
    assert auth._access_token == "new_token"
    mock_post.assert_called_once_with(
        url="http://token.com",
        auth=MockBasicAuth.return_value,
        data={"grant_type": "client_credentials"},
    )
    MockBasicAuth.assert_called_once_with(username="id", password="secret")


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_client_credentials_auth_fetch_token_no_access_token_in_response(
    mock_post,
):
    """Test ClientCredentialsAuth raises AuthError if access_token is missing from response."""
    mock_post.return_value = httpx.Response(
        200,
        json={"expires_in": 3600},
        request=httpx.Request("POST", "http://token.com"),
    )

    auth = ClientCredentialsAuth(
        client_id="id", client_secret="secret", token_url="http://token.com"
    )
    with pytest.raises(AuthError, match="Access token not found in token response."):
        await auth._fetch_access_token()


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_client_credentials_auth_fetch_token_http_error(mock_post):
    """Test ClientCredentialsAuth raises AuthError on HTTP status error."""
    mock_post.side_effect = httpx.HTTPStatusError(
        "Bad Request",
        request=httpx.Request("POST", "http://token.com"),
        response=httpx.Response(400),
    )

    auth = ClientCredentialsAuth(
        client_id="id", client_secret="secret", token_url="http://token.com"
    )
    with pytest.raises(AuthError, match="Failed to fetch access token: 400 - "):
        await auth._fetch_access_token()


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_client_credentials_auth_fetch_token_network_error(mock_post):
    """Test ClientCredentialsAuth raises AuthError on network error."""
    mock_post.side_effect = httpx.RequestError(
        "Network unreachable", request=httpx.Request("POST", "http://token.com")
    )

    auth = ClientCredentialsAuth(
        client_id="id", client_secret="secret", token_url="http://token.com"
    )
    with pytest.raises(
        AuthError, match="Failed to fetch access token: Network unreachable"
    ):
        await auth._fetch_access_token()


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_client_credentials_auth_authenticate_fetches_token(mock_post):
    """Test ClientCredentialsAuth fetches token if not already available."""
    mock_post.return_value = httpx.Response(
        200,
        json={"access_token": "new_token"},
        request=httpx.Request("POST", "http://token.com"),
    )

    auth = ClientCredentialsAuth(
        client_id="id", client_secret="secret", token_url="http://token.com"
    )
    request = httpx.Request("GET", "http://example.com")
    await auth.async_authenticate(request)

    assert request.headers["Authorization"] == "Bearer new_token"
    mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_client_credentials_auth_authenticate_uses_existing_token():
    """Test ClientCredentialsAuth uses existing token if available."""
    auth = ClientCredentialsAuth(
        client_id="id", client_secret="secret", token_url="http://token.com"
    )
    auth._access_token = "existing_token"  # Manually set existing token

    request = httpx.Request("GET", "http://example.com")
    await auth.async_authenticate(request)

    assert request.headers["Authorization"] == "Bearer existing_token"
    # Ensure _fetch_access_token was NOT called
    with patch.object(auth, "_fetch_access_token") as mock_fetch:
        await auth.async_authenticate(request)
        mock_fetch.assert_not_called()


@pytest.mark.asyncio
async def test_client_credentials_auth_close():
    """Test ClientCredentialsAuth closes its internal client."""
    auth = ClientCredentialsAuth(
        client_id="id", client_secret="secret", token_url="http://token.com"
    )
    # Manually initialize _token_client for testing close
    auth._token_client = httpx.AsyncClient()
    with patch.object(auth._token_client, "aclose") as mock_aclose:
        await auth.async_close()
        mock_aclose.assert_called_once()
        assert auth._token_client is None


@pytest.mark.asyncio
async def test_client_credentials_auth_close_no_client():
    """Test ClientCredentialsAuth close method handles no internal client gracefully."""
    auth = ClientCredentialsAuth(
        client_id="id", client_secret="secret", token_url="http://token.com"
    )
    auth._token_client = None  # Ensure no client
    await auth.async_close()
    # No exception means it passed
