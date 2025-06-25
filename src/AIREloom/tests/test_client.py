import json
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from bibliofabric.auth import ClientCredentialsAuth, NoAuth, StaticTokenAuth
from bibliofabric.exceptions import (
    APIError,
    AuthError,
    NetworkError,
    TimeoutError,
)
from cachetools import TTLCache  # Needed for the factory
from pydantic import BaseModel  # Added for test model
from pytest_httpx import HTTPXMock

from aireloom.client import AireloomClient
from aireloom.config import ApiSettings
from aireloom.constants import (
    OPENAIRE_GRAPH_API_BASE_URL,
    OPENAIRE_SCHOLIX_API_BASE_URL,
)

# --- Constants for Testing ---
MOCK_BASE_URL = "https://api.test.com"
MOCK_STATIC_TOKEN = "static_test_token"
MOCK_CLIENT_ID = "client_test_id"
MOCK_CLIENT_SECRET = "client_test_secret"
MOCK_OAUTH_TOKEN = "oauth_test_token"
MOCK_TOKEN_URL = "https://token.test.com/token"
MOCK_USER_AGENT = "Test User Agent"


# --- Test Pydantic Model ---
class MockResource(BaseModel):
    id: int
    name: str
    value: float | None = None


# --- Fixtures ---
@pytest.fixture
def mock_settings() -> ApiSettings:
    """Fixture for mock API settings."""
    return ApiSettings(
        openaire_api_token=None,  # Default to no token
        openaire_client_id=None,  # Default to no client creds
        openaire_client_secret=None,
        openaire_token_url=MOCK_TOKEN_URL,
        request_timeout=10,
        max_retries=2,
        backoff_factor=0.5,
        user_agent=MOCK_USER_AGENT,
    )


@pytest.fixture
def mock_settings_with_token() -> ApiSettings:
    """Fixture for mock API settings with a static token."""
    return ApiSettings(
        openaire_api_token=MOCK_STATIC_TOKEN,
        openaire_client_id=None,
        openaire_client_secret=None,
        openaire_token_url=MOCK_TOKEN_URL,
        request_timeout=10,
        max_retries=2,
        backoff_factor=0.5,
        user_agent=MOCK_USER_AGENT,
    )


@pytest.fixture
def mock_settings_with_creds() -> ApiSettings:
    """Fixture for mock API settings with client credentials."""
    return ApiSettings(
        openaire_api_token=None,
        openaire_client_id=MOCK_CLIENT_ID,
        openaire_client_secret=MOCK_CLIENT_SECRET,
        openaire_token_url=MOCK_TOKEN_URL,
        request_timeout=10,
        max_retries=2,
        backoff_factor=0.5,
        user_agent=MOCK_USER_AGENT,
    )


@pytest.fixture
def mock_settings_caching_enabled() -> ApiSettings:
    """Fixture for mock API settings with caching enabled."""
    return ApiSettings(
        openaire_api_token=None,
        openaire_client_id=None,
        openaire_client_secret=None,
        openaire_token_url=MOCK_TOKEN_URL,
        request_timeout=10,
        max_retries=2,
        backoff_factor=0.5,
        user_agent=MOCK_USER_AGENT,
        enable_caching=True,
        cache_ttl_seconds=300,
        cache_max_size=128,
    )


@pytest.fixture
def mock_settings_caching_disabled() -> ApiSettings:
    """Fixture for mock API settings with caching explicitly disabled."""
    return ApiSettings(
        openaire_api_token=None,
        openaire_client_id=None,
        openaire_client_secret=None,
        openaire_token_url=MOCK_TOKEN_URL,
        request_timeout=10,
        max_retries=2,
        backoff_factor=0.5,
        user_agent=MOCK_USER_AGENT,
        enable_caching=False,  # Explicitly false
        cache_ttl_seconds=300,
        cache_max_size=128,
    )


# --- Test Client Initialization ---


def test_client_init_no_auth_default(mock_settings):
    """Test client initialization uses NoAuth by default when no creds provided."""
    client = AireloomClient(settings=mock_settings, base_url=MOCK_BASE_URL)
    assert isinstance(client._auth_strategy, NoAuth)
    assert client._base_url == MOCK_BASE_URL
    assert client._http_client.timeout.read == mock_settings.request_timeout
    assert client._http_client.headers["User-Agent"] == MOCK_USER_AGENT


@pytest.mark.asyncio
async def test_client_init_no_auth_explicit(mock_settings):
    """Test client initialization with explicit NoAuth strategy."""
    auth_strategy = NoAuth()
    client = AireloomClient(settings=mock_settings, auth_strategy=auth_strategy)
    assert client._auth_strategy is auth_strategy
    await client.aclose()


def test_client_init_static_token_from_settings(mock_settings_with_token):
    """Test client initialization uses StaticTokenAuth from settings."""
    client = AireloomClient(settings=mock_settings_with_token)
    assert isinstance(client._auth_strategy, StaticTokenAuth)
    assert client._auth_strategy._token == MOCK_STATIC_TOKEN


def test_client_init_static_token_override(mock_settings):
    """Test client initialization uses StaticTokenAuth with override."""
    client = AireloomClient(settings=mock_settings, api_token="override_token")
    assert isinstance(client._auth_strategy, StaticTokenAuth)
    assert client._auth_strategy._token == "override_token"


def test_client_init_client_creds_from_settings(mock_settings_with_creds):
    """Test client initialization uses ClientCredentialsAuth from settings."""
    client = AireloomClient(settings=mock_settings_with_creds)
    assert isinstance(client._auth_strategy, ClientCredentialsAuth)
    assert client._auth_strategy._client_id == MOCK_CLIENT_ID
    assert client._auth_strategy._client_secret == MOCK_CLIENT_SECRET
    assert client._auth_strategy._token_url == MOCK_TOKEN_URL


def test_client_init_client_creds_override(mock_settings):
    """Test client initialization uses ClientCredentialsAuth with overrides."""
    client = AireloomClient(
        settings=mock_settings, client_id="override_id", client_secret="override_secret"
    )
    assert isinstance(client._auth_strategy, ClientCredentialsAuth)
    assert client._auth_strategy._client_id == "override_id"
    assert client._auth_strategy._client_secret == "override_secret"
    assert client._auth_strategy._token_url == MOCK_TOKEN_URL  # From settings


def test_client_init_creds_precedence_over_token(mock_settings_with_creds):
    """Test client credentials take precedence over static token in settings."""
    settings = mock_settings_with_creds
    settings.openaire_api_token = MOCK_STATIC_TOKEN  # Add a token too
    client = AireloomClient(settings=settings)
    # Should still use ClientCredentialsAuth
    assert isinstance(client._auth_strategy, ClientCredentialsAuth)


def test_client_init_explicit_auth_precedence(mock_settings_with_creds):
    """Test explicit auth strategy takes precedence over settings."""
    explicit_auth = StaticTokenAuth(token="explicit_token")
    client = AireloomClient(
        settings=mock_settings_with_creds, auth_strategy=explicit_auth
    )
    assert client._auth_strategy is explicit_auth


# --- Test Request Execution and Authentication ---


@pytest.mark.asyncio
async def test_request_with_no_auth(mock_settings, httpx_mock: HTTPXMock):
    """Test a request is made without Authorization header using NoAuth."""
    url = f"{MOCK_BASE_URL}/test"
    httpx_mock.add_response(
        url=url, method="GET", status_code=httpx.codes.OK, json={"ok": True}
    )
    client = AireloomClient(settings=mock_settings, base_url=MOCK_BASE_URL)

    async with client:
        response = await client.request("GET", "/test")

    assert response.status_code == httpx.codes.OK
    assert response.json() == {"ok": True}
    requests = httpx_mock.get_requests(url=url)
    assert len(requests) == 1
    assert "Authorization" not in requests[0].headers
    assert requests[0].headers["User-Agent"] == MOCK_USER_AGENT


@pytest.mark.asyncio
async def test_request_with_static_token_auth(
    mock_settings_with_token, httpx_mock: HTTPXMock
):
    """Test a request includes correct Authorization header with StaticTokenAuth."""
    url = f"{MOCK_BASE_URL}/test"
    httpx_mock.add_response(
        url=url, method="GET", status_code=httpx.codes.OK, json={"ok": True}
    )
    client = AireloomClient(settings=mock_settings_with_token, base_url=MOCK_BASE_URL)

    async with client:
        response = await client.request("GET", "/test")

    assert response.status_code == httpx.codes.OK
    requests = httpx_mock.get_requests(url=url)
    assert len(requests) == 1
    assert requests[0].headers["Authorization"] == f"Bearer {MOCK_STATIC_TOKEN}"
    assert requests[0].headers["User-Agent"] == MOCK_USER_AGENT


@pytest.mark.asyncio
async def test_request_with_client_creds_auth_success(
    mock_settings_with_creds, httpx_mock: HTTPXMock
):
    """Test a request with ClientCredentialsAuth fetches token and uses it."""
    # Mock the token endpoint
    httpx_mock.add_response(
        url=MOCK_TOKEN_URL,
        method="POST",
        json={"access_token": MOCK_OAUTH_TOKEN, "expires_in": 3600},
        status_code=httpx.codes.OK,
    )
    # Mock the actual API endpoint
    api_url = f"{MOCK_BASE_URL}/data"
    httpx_mock.add_response(
        url=api_url, method="GET", status_code=httpx.codes.OK, json={"data": "value"}
    )

    client = AireloomClient(settings=mock_settings_with_creds, base_url=MOCK_BASE_URL)

    async with client:
        response = await client.request("GET", "/data")

    assert response.status_code == httpx.codes.OK
    assert response.json() == {"data": "value"}

    # Check token request
    token_requests = httpx_mock.get_requests(url=MOCK_TOKEN_URL, method="POST")
    assert len(token_requests) == 1
    assert (
        token_requests[0].headers["Authorization"].startswith("Basic ")
    )  # Basic auth used

    # Check API request
    api_requests = httpx_mock.get_requests(url=api_url, method="GET")
    assert len(api_requests) == 1
    assert api_requests[0].headers["Authorization"] == f"Bearer {MOCK_OAUTH_TOKEN}"
    assert api_requests[0].headers["User-Agent"] == MOCK_USER_AGENT


@pytest.mark.asyncio
async def test_request_with_client_creds_auth_token_failure(
    mock_settings_with_creds, httpx_mock: HTTPXMock
):
    """Test that AuthError during token fetch prevents API call and propagates."""
    # Mock the token endpoint to fail
    httpx_mock.add_response(
        url=MOCK_TOKEN_URL, method="POST", status_code=401, text="Invalid Credentials"
    )
    # Do NOT mock the /data endpoint

    client = AireloomClient(settings=mock_settings_with_creds, base_url=MOCK_BASE_URL)
    with pytest.raises(AuthError, match="Failed to fetch access token: 401"):
        async with client:
            await client.request("GET", "/data")
    # Ensure the API endpoint was never called
    api_requests = httpx_mock.get_requests(url=f"{MOCK_BASE_URL}/data", method="GET")
    assert len(api_requests) == 0


# --- Test Retries and Error Handling ---


@pytest.mark.asyncio
async def test_request_retry_on_503(mock_settings, httpx_mock: HTTPXMock):
    """Test that the client retries on 503 status code."""
    url = f"{MOCK_BASE_URL}/retry_test"
    httpx_mock.add_response(
        url=url, method="GET", status_code=503
    )  # First attempt fails
    httpx_mock.add_response(
        url=url, method="GET", status_code=503
    )  # Second attempt fails
    httpx_mock.add_response(
        url=url, method="GET", status_code=httpx.codes.OK, json={"ok": True}
    )  # Third succeeds

    client = AireloomClient(
        settings=mock_settings, base_url=MOCK_BASE_URL
    )  # max_retries = 2

    async with client:
        response = await client.request("GET", "/retry_test")

    assert response.status_code == httpx.codes.OK
    assert response.json() == {"ok": True}
    requests = httpx_mock.get_requests(url=url)
    assert len(requests) == 3  # Initial + 2 retries
    assert requests[0].headers["User-Agent"] == MOCK_USER_AGENT
    assert requests[1].headers["User-Agent"] == MOCK_USER_AGENT
    assert requests[2].headers["User-Agent"] == MOCK_USER_AGENT


@pytest.mark.asyncio
async def test_request_retry_on_rate_limit(mock_settings, httpx_mock: HTTPXMock):
    """Test that the client retries on 429 status code."""
    url = f"{MOCK_BASE_URL}/rate_limit_test"
    httpx_mock.add_response(
        url=url, method="GET", status_code=429
    )  # First attempt fails
    httpx_mock.add_response(
        url=url, method="GET", status_code=httpx.codes.OK, json={"ok": True}
    )  # Second succeeds

    # Use only 1 retry for this test
    mock_settings.max_retries = 1
    client = AireloomClient(settings=mock_settings, base_url=MOCK_BASE_URL)

    async with client:
        response = await client.request("GET", "/rate_limit_test")

    assert response.status_code == httpx.codes.OK
    assert response.json() == {"ok": True}
    requests = httpx_mock.get_requests(url=url)
    assert len(requests) == 2  # Initial + 1 retry
    assert requests[0].headers["User-Agent"] == MOCK_USER_AGENT
    assert requests[1].headers["User-Agent"] == MOCK_USER_AGENT


@pytest.mark.asyncio
async def test_request_failure_after_retries(mock_settings, httpx_mock: HTTPXMock):
    """Test that ApiError is raised after exhausting retries."""
    url = f"{MOCK_BASE_URL}/fail_test"
    httpx_mock.add_response(url=url, method="GET", status_code=500)  # Attempt 1
    httpx_mock.add_response(url=url, method="GET", status_code=502)  # Attempt 2
    httpx_mock.add_response(
        url=url, method="GET", status_code=504
    )  # Attempt 3 (max_retries = 2)

    client = AireloomClient(
        settings=mock_settings, base_url=MOCK_BASE_URL
    )  # max_retries = 2

    with pytest.raises(APIError) as excinfo:
        async with client:
            await client.request("GET", "/fail_test")

    assert len(httpx_mock.get_requests(url=url)) == 3
    assert excinfo.value.response is not None
    assert excinfo.value.response.status_code == 504  # Last error encountered
    assert "API request failed with status 504" in str(excinfo.value)
    requests = httpx_mock.get_requests(url=url)
    assert requests[0].headers["User-Agent"] == MOCK_USER_AGENT
    assert requests[1].headers["User-Agent"] == MOCK_USER_AGENT
    assert requests[2].headers["User-Agent"] == MOCK_USER_AGENT


@pytest.mark.asyncio
async def test_request_non_retryable_4xx_error(mock_settings, httpx_mock: HTTPXMock):
    """Test that ApiError is raised immediately for non-retryable 4xx errors."""
    url = f"{MOCK_BASE_URL}/client_error_test"
    httpx_mock.add_response(url=url, method="GET", status_code=404, text="Not Found")

    client = AireloomClient(settings=mock_settings, base_url=MOCK_BASE_URL)

    with pytest.raises(APIError) as excinfo:
        async with client:
            await client.request("GET", "/client_error_test")

    assert len(httpx_mock.get_requests(url=url)) == 1  # No retries
    assert excinfo.value.response is not None
    assert excinfo.value.response.status_code == 404
    assert "API request failed with status 404" in str(excinfo.value)
    requests = httpx_mock.get_requests(url=url)
    assert requests[0].headers["User-Agent"] == MOCK_USER_AGENT


@pytest.mark.asyncio
async def test_request_timeout_error(mock_settings, httpx_mock: HTTPXMock):
    """Test that TimeoutError is raised on timeout."""
    url = f"{MOCK_BASE_URL}/timeout_test"
    for _ in range(mock_settings.max_retries + 1):
        httpx_mock.add_exception(
            httpx.TimeoutException(
                "Request timed out", request=httpx.Request("GET", url)
            )
        )

    client = AireloomClient(settings=mock_settings, base_url=MOCK_BASE_URL)
    with pytest.raises(TimeoutError, match="Request timed out"):
        async with client:
            await client.request("GET", "/timeout_test")

    # Retries should have happened (initial + max_retries)
    requests = httpx_mock.get_requests(url=url)
    assert len(requests) >= 1
    assert requests[0].headers["User-Agent"] == MOCK_USER_AGENT


@pytest.mark.asyncio
async def test_request_network_error(mock_settings, httpx_mock: HTTPXMock):
    """Test that NetworkError is raised on connection error."""
    url = f"{MOCK_BASE_URL}/network_error_test"
    # Register the exception for each retry attempt
    for _ in range(mock_settings.max_retries + 1):
        httpx_mock.add_exception(
            httpx.ConnectError("Connection failed", request=httpx.Request("GET", url))
        )

    client = AireloomClient(settings=mock_settings, base_url=MOCK_BASE_URL)
    with pytest.raises(NetworkError, match="Network error occurred"):
        async with client:
            await client.request("GET", "/network_error_test")

    requests = httpx_mock.get_requests(url=url)
    assert (
        len(requests) == mock_settings.max_retries + 1
    )  # Should retry on connect error
    assert requests[0].headers["User-Agent"] == MOCK_USER_AGENT


# --- Test Client Context Manager and Closing ---


@pytest.mark.asyncio
async def test_client_aclose(mock_settings_with_creds):
    """Test that aclose closes the http client and the auth strategy client."""
    # Mock the ClientCredentialsAuth close method
    mock_auth_close = AsyncMock()

    with patch(
        "aireloom.client.ClientCredentialsAuth", spec=ClientCredentialsAuth
    ) as MockAuth:
        mock_auth_instance = MockAuth.return_value
        mock_auth_instance.async_close = mock_auth_close

        # Mock the httpx client's aclose method
        mock_http_client = MagicMock(spec=httpx.AsyncClient)
        mock_http_client.aclose = AsyncMock()

        # Create client with the mocked http client
        client = AireloomClient(
            settings=mock_settings_with_creds, http_client=mock_http_client
        )

        # Verify the mock auth was used
        assert client._auth_strategy is mock_auth_instance
        # Prevent closing the client we passed in
        client._should_close_client = False

        await client.aclose()

        # Assert auth strategy close was called
        mock_auth_close.assert_awaited_once()
        # Assert http client close was *not* called (because we provided it)
        mock_http_client.aclose.assert_not_awaited()

        # Test again, this time letting the client create its own http client
        client_creates_http = AireloomClient(settings=mock_settings_with_creds)
        # Manually replace auth strategy with our mock that has mocked close
        client_creates_http._auth_strategy = mock_auth_instance

        real_http_client = client_creates_http._http_client
        with patch.object(
            real_http_client, "aclose", new_callable=AsyncMock
        ) as mock_real_aclose:
            await client_creates_http.aclose()

            # Assert auth strategy close was called again
            assert mock_auth_close.call_count == 2
            # Assert the internal http client's close *was* called
            mock_real_aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_client_context_manager(mock_settings):
    """Test the client works as an async context manager."""
    client = AireloomClient(settings=mock_settings)
    # Mock aclose to check if it's called
    client.aclose = AsyncMock()

    async with client:
        assert isinstance(client, AireloomClient)
        # Perform some action (optional)

    # Assert aclose was called upon exiting the context
    client.aclose.assert_awaited_once()


# --- Test Base URL Handling ---


@pytest.mark.asyncio
async def test_base_url_override(mock_settings, httpx_mock: HTTPXMock):
    """Test that base_url_override works correctly."""
    default_url = f"{MOCK_BASE_URL}/default"
    override_url = "https://override.api.com/override"

    httpx_mock.add_response(
        url=default_url,
        method="GET",
        status_code=httpx.codes.OK,
        json={"ok": "default"},
    )
    httpx_mock.add_response(
        url=override_url,
        method="GET",
        status_code=httpx.codes.OK,
        json={"ok": "override"},
    )

    client = AireloomClient(settings=mock_settings, base_url=MOCK_BASE_URL)

    async with client:
        # Request to default base URL
        resp1 = await client.request("GET", "/default")
        # Request with override
        resp2 = await client.request(
            "GET", "/override", base_url_override="https://override.api.com"
        )

    assert resp1.json() == {"ok": "default"}
    assert resp2.json() == {"ok": "override"}

    requests = httpx_mock.get_requests()
    assert len(requests) == 2
    assert str(requests[0].url) == default_url
    assert str(requests[1].url) == override_url
    assert requests[0].headers["User-Agent"] == MOCK_USER_AGENT
    assert requests[1].headers["User-Agent"] == MOCK_USER_AGENT


@pytest.mark.asyncio
async def test_default_base_urls_used(mock_settings, httpx_mock: HTTPXMock):
    """Test that the correct default OpenAIRE base URLs are used if not overridden."""
    graph_url = f"{OPENAIRE_GRAPH_API_BASE_URL.rstrip('/')}/graph_test"
    # Example using Scholix URL via override for testing constants
    scholix_url = f"{OPENAIRE_SCHOLIX_API_BASE_URL.rstrip('/')}/scholix_test"

    httpx_mock.add_response(url=graph_url, method="GET", status_code=httpx.codes.OK)
    httpx_mock.add_response(url=scholix_url, method="GET", status_code=httpx.codes.OK)

    # Client defaults to Graph API base URL
    client = AireloomClient(settings=mock_settings)
    assert client._base_url == OPENAIRE_GRAPH_API_BASE_URL.rstrip("/")

    async with client:
        # Request using default base URL (Graph)
        await client.request("GET", "/graph_test")
        # Request overriding to Scholix base URL
        await client.request(
            "GET", "/scholix_test", base_url_override=OPENAIRE_SCHOLIX_API_BASE_URL
        )

    requests = httpx_mock.get_requests()
    assert len(requests) == 2
    assert str(requests[0].url) == graph_url
    assert str(requests[1].url) == scholix_url
    assert requests[0].headers["User-Agent"] == MOCK_USER_AGENT
    assert requests[1].headers["User-Agent"] == MOCK_USER_AGENT


# --- Test Request Parameters and Methods ---


@pytest.mark.asyncio
async def test_request_post_with_json(mock_settings, httpx_mock: HTTPXMock):
    """Test POST request with JSON body."""
    url = f"{MOCK_BASE_URL}/post_test"
    payload = {"key": "value", "num": 1}
    httpx_mock.add_response(
        url=url, method="POST", status_code=201, json={"created": True}
    )
    client = AireloomClient(settings=mock_settings, base_url=MOCK_BASE_URL)

    async with client:
        response = await client.request("POST", "/post_test", json=payload)

    assert response.status_code == 201
    assert response.json() == {"created": True}
    requests = httpx_mock.get_requests(url=url, method="POST")
    assert len(requests) == 1
    request = requests[0]
    # Compare parsed JSON instead of raw string to avoid whitespace issues
    # Use separators=(',', ':') to match httpx's compact encoding
    assert request.read() == json.dumps(payload, separators=(",", ":")).encode("utf-8")
    assert request.headers["Content-Type"] == "application/json"
    assert request.headers["User-Agent"] == MOCK_USER_AGENT


@pytest.mark.asyncio
async def test_request_get_with_params(mock_settings, httpx_mock: HTTPXMock):
    """Test GET request with query parameters."""
    # httpx encodes parameters, so the matched URL should reflect that
    expected_url_encoded = f"{MOCK_BASE_URL}/get_test?param1=value1&param2=123"
    httpx_mock.add_response(
        url=expected_url_encoded, method="GET", status_code=200, json={"ok": True}
    )
    client = AireloomClient(settings=mock_settings, base_url=MOCK_BASE_URL)
    params = {"param1": "value1", "param2": 123}  # Mix of str and int

    async with client:
        response = await client.request("GET", "/get_test", params=params)

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    # Verify the request URL was correctly encoded by httpx
    requests = httpx_mock.get_requests(url=expected_url_encoded, method="GET")
    assert len(requests) == 1
    request = requests[0]
    assert request.headers["User-Agent"] == MOCK_USER_AGENT


# --- Test Rate Limiting ---


@pytest.mark.asyncio
@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_client_preemptive_delay_low_remaining(
    mock_sleep: AsyncMock, httpx_mock: HTTPXMock, mock_settings: ApiSettings
):
    """Test client waits before request if X-RateLimit-Remaining is low."""
    settings = mock_settings
    settings.enable_rate_limiting = True
    settings.rate_limit_buffer_percentage = 0.1  # Buffer is 10%
    # Disable tenacity retries to isolate rate limit sleep
    settings.max_retries = 0

    client = AireloomClient(settings=settings, base_url=MOCK_BASE_URL)

    reset_time_dt = datetime.now(UTC) + timedelta(seconds=10)
    reset_timestamp_str = str(int(reset_time_dt.timestamp()))

    # First response: low remaining requests, reset time in future
    httpx_mock.add_response(
        url=f"{MOCK_BASE_URL}/test1",
        method="GET",
        headers={
            "X-RateLimit-Limit": "100",
            "X-RateLimit-Remaining": "5",  # 5% remaining, buffer is 10%, so wait
            "X-RateLimit-Reset": reset_timestamp_str,
        },
        json={"id": "1", "title": "Test 1"},
    )
    # Second response: for the request that should trigger the wait
    httpx_mock.add_response(
        url=f"{MOCK_BASE_URL}/test2",
        method="GET",
        json={"id": "2", "title": "Test 2"},
    )

    async with client:
        # First request populates rate limit headers
        await client.request("GET", "/test1")
        mock_sleep.assert_not_called()  # No sleep before or during the first request

        # Second request should trigger pre-emptive sleep
        await client.request("GET", "/test2")

    # Assert sleep was called once
    mock_sleep.assert_called_once()
    args, _ = mock_sleep.call_args
    # Check sleep duration is close to the reset time (allowing for small processing delays)
    # The client calculates delay as: reset_timestamp - time.time()
    # We expect it to be around 10 seconds.
    assert 8 < args[0] <= 10.5  # Allow a bit of leeway


@pytest.mark.asyncio
async def test_client_429_with_retry_after_seconds(
    httpx_mock: HTTPXMock, mock_settings: ApiSettings
):
    """Test client handles 429 with Retry-After header (seconds) via tenacity."""
    settings = mock_settings
    settings.enable_rate_limiting = True
    settings.max_retries = 1  # Allow one retry to test tenacity behavior

    client = AireloomClient(settings=settings, base_url=MOCK_BASE_URL)

    # First response: 429 with Retry-After header
    httpx_mock.add_response(
        url=f"{MOCK_BASE_URL}/limited",
        method="GET",
        status_code=429,
        headers={"Retry-After": "15"},
    )
    # Second response: Success after retry
    httpx_mock.add_response(
        url=f"{MOCK_BASE_URL}/limited",
        method="GET",
        status_code=200,
        json={"ok": True},
    )

    async with client:
        response = await client.request("GET", "/limited")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    # Verify both requests were made (initial + retry)
    requests = httpx_mock.get_requests(url=f"{MOCK_BASE_URL}/limited")
    assert len(requests) == 2


@pytest.mark.asyncio
async def test_client_429_with_retry_after_http_date(
    httpx_mock: HTTPXMock, mock_settings: ApiSettings
):
    """Test client handles 429 with Retry-After header (HTTP-date) via tenacity."""
    settings = mock_settings
    settings.enable_rate_limiting = True
    settings.max_retries = 1  # Allow one retry to test tenacity behavior

    client = AireloomClient(settings=settings, base_url=MOCK_BASE_URL)

    retry_after_dt = datetime.now(UTC) + timedelta(seconds=20)
    # Format as RFC 1123 (HTTP-date)
    retry_after_http_date = retry_after_dt.strftime("%a, %d %b %Y %H:%M:%S GMT")

    # First response: 429 with Retry-After header (HTTP date)
    httpx_mock.add_response(
        url=f"{MOCK_BASE_URL}/limited_date",
        method="GET",
        status_code=429,
        headers={"Retry-After": retry_after_http_date},
    )
    # Second response: Success after retry
    httpx_mock.add_response(
        url=f"{MOCK_BASE_URL}/limited_date",
        method="GET",
        status_code=200,
        json={"ok": True},
    )

    async with client:
        response = await client.request("GET", "/limited_date")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    # Verify both requests were made (initial + retry)
    requests = httpx_mock.get_requests(url=f"{MOCK_BASE_URL}/limited_date")
    assert len(requests) == 2


@pytest.mark.asyncio
async def test_client_429_with_no_retry_after(
    httpx_mock: HTTPXMock, mock_settings: ApiSettings
):
    """Test client handles 429 without Retry-After header via tenacity."""
    settings = mock_settings
    settings.enable_rate_limiting = True
    settings.max_retries = 1  # Allow one retry to test tenacity behavior

    client = AireloomClient(settings=settings, base_url=MOCK_BASE_URL)

    # First response: 429 without Retry-After header
    httpx_mock.add_response(
        url=f"{MOCK_BASE_URL}/limited_no_header",
        method="GET",
        status_code=429,
        # No Retry-After header
    )
    # Second response: Success after retry
    httpx_mock.add_response(
        url=f"{MOCK_BASE_URL}/limited_no_header",
        method="GET",
        status_code=200,
        json={"ok": True},
    )

    async with client:
        response = await client.request("GET", "/limited_no_header")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    # Verify both requests were made (initial + retry)
    requests = httpx_mock.get_requests(url=f"{MOCK_BASE_URL}/limited_no_header")
    assert len(requests) == 2


@pytest.mark.asyncio
@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_client_rate_limiting_disabled(
    mock_sleep: AsyncMock, httpx_mock: HTTPXMock, mock_settings: ApiSettings
):
    """Test asyncio.sleep is not called for rate limiting if disabled."""
    settings = mock_settings
    settings.enable_rate_limiting = False
    settings.max_retries = 0  # Disable tenacity retries to avoid its sleep

    client = AireloomClient(settings=settings, base_url=MOCK_BASE_URL)

    # Scenario 1: Low remaining (should be ignored)
    reset_time_dt = datetime.now(UTC) + timedelta(seconds=10)
    reset_timestamp_str = str(int(reset_time_dt.timestamp()))

    httpx_mock.add_response(
        url=f"{MOCK_BASE_URL}/test_disabled_low_remaining",
        method="GET",
        headers={
            "X-RateLimit-Limit": "100",
            "X-RateLimit-Remaining": "1",  # Very low
            "X-RateLimit-Reset": reset_timestamp_str,
        },
        json={"id": "1"},
    )
    # Second request to check if sleep was called pre-emptively
    httpx_mock.add_response(
        url=f"{MOCK_BASE_URL}/test_disabled_after_low",
        method="GET",
        json={"id": "2"},
    )

    # Scenario 2: 429 response (should be ignored by rate limiter, will raise APIError)
    httpx_mock.add_response(
        url=f"{MOCK_BASE_URL}/test_disabled_429",
        method="GET",
        status_code=429,
        headers={"Retry-After": "5"},  # This header should be ignored
    )

    async with client:
        # Test low remaining scenario
        await client.request("GET", "/test_disabled_low_remaining")
        mock_sleep.assert_not_called()  # No pre-emptive sleep
        await client.request("GET", "/test_disabled_after_low")
        mock_sleep.assert_not_called()  # Still no pre-emptive sleep

        # Test 429 scenario
        with pytest.raises(APIError) as excinfo:  # Expect APIError as tenacity is off
            await client.request("GET", "/test_disabled_429")

        assert excinfo.value.response is not None
        assert excinfo.value.response.status_code == 429

    # Assert sleep was never called by rate limiting logic
    mock_sleep.assert_not_called()


# --- Test Caching Logic ---


@pytest.mark.asyncio
async def test_cache_hit(
    mock_settings_caching_enabled: ApiSettings, httpx_mock: HTTPXMock
):
    """Test that a second identical GET request hits the cache."""
    client = AireloomClient(
        settings=mock_settings_caching_enabled, base_url=MOCK_BASE_URL
    )
    url_path = "/cached_resource"
    full_url = f"{MOCK_BASE_URL}{url_path}"
    mock_response_data = {"id": 1, "name": "Test Resource", "value": 1.23}
    expected_model = MockResource(**mock_response_data)

    # Mock only one HTTP response, the second call should be cached
    httpx_mock.add_response(
        url=full_url, method="GET", status_code=200, json=mock_response_data
    )

    async with client:
        # First call - should make HTTP request and cache
        response1 = await client.request("GET", url_path, expected_model=MockResource)
        # Second call - should hit cache
        response2 = await client.request("GET", url_path, expected_model=MockResource)

    assert response1 == expected_model
    assert response2 == expected_model
    assert response1 is response2  # Should be the same object from cache

    # Verify only one HTTP request was made
    requests = httpx_mock.get_requests(url=full_url, method="GET")
    assert len(requests) == 1


@pytest.mark.asyncio
async def test_cache_miss_different_url(
    mock_settings_caching_enabled: ApiSettings, httpx_mock: HTTPXMock
):
    """Test that different URLs result in cache misses and new HTTP calls."""
    client = AireloomClient(
        settings=mock_settings_caching_enabled, base_url=MOCK_BASE_URL
    )
    url_path1 = "/resourceA"
    url_path2 = "/resourceB"
    full_url1 = f"{MOCK_BASE_URL}{url_path1}"
    full_url2 = f"{MOCK_BASE_URL}{url_path2}"
    mock_data1 = {"id": 1, "name": "Resource A"}
    mock_data2 = {"id": 2, "name": "Resource B"}

    httpx_mock.add_response(
        url=full_url1, method="GET", status_code=200, json=mock_data1
    )
    httpx_mock.add_response(
        url=full_url2, method="GET", status_code=200, json=mock_data2
    )

    async with client:
        resp1 = await client.request("GET", url_path1, expected_model=MockResource)
        resp2 = await client.request("GET", url_path2, expected_model=MockResource)

    assert resp1 == MockResource(**mock_data1)
    assert resp2 == MockResource(**mock_data2)
    assert resp1 is not resp2

    assert len(httpx_mock.get_requests(url=full_url1, method="GET")) == 1
    assert len(httpx_mock.get_requests(url=full_url2, method="GET")) == 1


@pytest.mark.asyncio
async def test_cache_miss_different_params(
    mock_settings_caching_enabled: ApiSettings, httpx_mock: HTTPXMock
):
    """Test that different query parameters result in cache misses."""
    client = AireloomClient(
        settings=mock_settings_caching_enabled, base_url=MOCK_BASE_URL
    )
    url_path = "/param_resource"
    # httpx_mock needs the full URL including params for matching
    full_url_p1 = f"{MOCK_BASE_URL}{url_path}?filter=A"
    full_url_p2 = f"{MOCK_BASE_URL}{url_path}?filter=B"
    full_url_p3 = (
        f"{MOCK_BASE_URL}{url_path}?filter=A&sort=name"  # Different combination
    )

    mock_data_p1 = {"id": 1, "name": "Filtered A"}
    mock_data_p2 = {"id": 2, "name": "Filtered B"}
    mock_data_p3 = {"id": 3, "name": "Filtered A Sorted"}

    httpx_mock.add_response(
        url=full_url_p1, method="GET", status_code=200, json=mock_data_p1
    )
    httpx_mock.add_response(
        url=full_url_p2, method="GET", status_code=200, json=mock_data_p2
    )
    httpx_mock.add_response(
        url=full_url_p3, method="GET", status_code=200, json=mock_data_p3
    )
    # p4 should hit the cache for p3 due to sorted param key generation
    # So, no separate httpx_mock.add_response for full_url_p4

    async with client:
        resp1 = await client.request(
            "GET", url_path, params={"filter": "A"}, expected_model=MockResource
        )
        resp2 = await client.request(
            "GET", url_path, params={"filter": "B"}, expected_model=MockResource
        )
        resp3 = await client.request(
            "GET",
            url_path,
            params={"filter": "A", "sort": "name"},
            expected_model=MockResource,
        )
        resp4 = await client.request(
            "GET",
            url_path,
            params={"sort": "name", "filter": "A"},
            expected_model=MockResource,
        )

    assert resp1 == MockResource(**mock_data_p1)
    assert resp2 == MockResource(**mock_data_p2)
    assert resp3 == MockResource(**mock_data_p3)
    assert resp4 == resp3  # Should be a cache hit from resp3

    assert len(httpx_mock.get_requests(url=full_url_p1, method="GET")) == 1
    assert len(httpx_mock.get_requests(url=full_url_p2, method="GET")) == 1
    assert len(httpx_mock.get_requests(url=full_url_p3, method="GET")) == 1
    # Total GET requests to the base path /param_resource should be 3
    assert len(httpx_mock.get_requests(method="GET")) == 3


@pytest.mark.asyncio
# @patch(...) # Removing this problematic patch decorator entirely
async def test_cache_ttl_expiration(
    # mock_time: MagicMock, # Parameter removed, will be created manually
    mock_settings_caching_enabled: ApiSettings,
    httpx_mock: HTTPXMock,
):
    """Test that cache entries expire after TTL."""
    ttl_seconds = 10  # Use a short TTL for testing
    mock_settings_caching_enabled.cache_ttl_seconds = ttl_seconds

    # 1. Create our own mock timer
    mock_timer = MagicMock()
    initial_numeric_timestamp = 1000.0
    mock_timer.return_value = initial_numeric_timestamp
    current_time = initial_numeric_timestamp  # For relative advancement

    # 2. Define a factory for TTLCache that uses our mock_timer
    # It needs to accept maxsize and ttl as TTLCache constructor does.
    def ttl_cache_factory(
        maxsize, ttl, timer=None, getsizeof=None
    ):  # Add all relevant TTLCache params
        # We ignore the passed 'timer' and always use our mock_timer
        return TTLCache(maxsize=maxsize, ttl=ttl, timer=mock_timer, getsizeof=getsizeof)

    # 3. Patch TTLCache where it's used in aireloom.client
    with patch("aireloom.client.TTLCache", new=ttl_cache_factory):
        client = AireloomClient(
            settings=mock_settings_caching_enabled, base_url=MOCK_BASE_URL
        )
        # Now, client._cache will be an instance of TTLCache
        # that uses our mock_timer.

        url_path = "/ttl_resource"
        full_url = f"{MOCK_BASE_URL}{url_path}"
        mock_data_initial = {"id": 1, "name": "Initial Data"}
        mock_data_refreshed = {"id": 2, "name": "Refreshed Data"}

        httpx_mock.add_response(
            url=full_url, method="GET", status_code=200, json=mock_data_initial
        )
        httpx_mock.add_response(
            url=full_url, method="GET", status_code=200, json=mock_data_refreshed
        )

        async with client:
            # First call - caches the item
            resp1 = await client.request("GET", url_path, expected_model=MockResource)
            assert resp1 == MockResource(**mock_data_initial)
            assert len(httpx_mock.get_requests(url=full_url, method="GET")) == 1

            # Second call immediately - should hit cache
            resp2 = await client.request("GET", url_path, expected_model=MockResource)
            assert resp2 == resp1  # Cache hit
            assert len(httpx_mock.get_requests(url=full_url, method="GET")) == 1

            # Advance time beyond TTL
            mock_timer.return_value = (
                current_time + ttl_seconds + 5
            )  # 5 seconds past TTL
            if client._cache:  # Check if cache exists before calling expire
                client._cache.expire()  # Manually expire items based on new time

            # Third call - should be a cache miss due to TTL, makes new HTTP request
            resp3 = await client.request("GET", url_path, expected_model=MockResource)
            assert resp3 == MockResource(**mock_data_refreshed)
            assert resp3 is not resp1  # New object
            assert len(httpx_mock.get_requests(url=full_url, method="GET")) == 2


@pytest.mark.asyncio
async def test_cache_disabled(
    mock_settings_caching_disabled: ApiSettings, httpx_mock: HTTPXMock
):
    """Test that no caching occurs if enable_caching is False."""
    client = AireloomClient(
        settings=mock_settings_caching_disabled, base_url=MOCK_BASE_URL
    )
    url_path = "/disabled_cache_resource"
    full_url = f"{MOCK_BASE_URL}{url_path}"
    mock_data = {"id": 1, "name": "No Cache Data"}

    # Mock two responses, as both calls should hit the server
    httpx_mock.add_response(url=full_url, method="GET", status_code=200, json=mock_data)
    httpx_mock.add_response(url=full_url, method="GET", status_code=200, json=mock_data)

    async with client:
        resp1 = await client.request("GET", url_path, expected_model=MockResource)
        resp2 = await client.request("GET", url_path, expected_model=MockResource)

    assert resp1 == MockResource(**mock_data)
    assert resp2 == MockResource(**mock_data)
    assert resp1 is not resp2  # Should be different objects

    assert len(httpx_mock.get_requests(url=full_url, method="GET")) == 2


@pytest.mark.asyncio
async def test_non_get_requests_not_cached(
    mock_settings_caching_enabled: ApiSettings, httpx_mock: HTTPXMock
):
    """Test that non-GET requests (e.g., POST) are not cached or retrieved from cache."""
    client = AireloomClient(
        settings=mock_settings_caching_enabled, base_url=MOCK_BASE_URL
    )
    url_path = "/post_resource"
    full_url = f"{MOCK_BASE_URL}{url_path}"
    post_payload = {"data": "sample"}
    mock_response_data = {"id": 1, "status": "created"}

    # Mock two POST responses, as caching should not apply
    httpx_mock.add_response(
        url=full_url, method="POST", status_code=201, json=mock_response_data
    )
    httpx_mock.add_response(
        url=full_url, method="POST", status_code=201, json=mock_response_data
    )

    async with client:
        # First POST call
        await client.request(
            "POST",
            url_path,
            json=post_payload,
            expected_model=MockResource,  # Using MockResource for structure
        )
        # Second POST call (identical)
        await client.request(
            "POST", url_path, json=post_payload, expected_model=MockResource
        )

    # Assuming MockResource can handle 'status' if 'name' is optional or has default
    # For this test, we mainly care about the HTTP call count.
    # If MockResource needs 'name', adjust mock_response_data or expected_model usage.
    # Let's assume MockResource is flexible or we adapt the response.
    # For simplicity, let's assume the response can be parsed by MockResource if id is present.
    # A more specific model for POST response might be better in a real scenario.
    # Here, we'll just check the HTTP call count.

    assert len(httpx_mock.get_requests(url=full_url, method="POST")) == 2

    # Also, try a GET request to the same path to ensure it's not polluted by POST
    get_mock_data = {"id": 10, "name": "GET response"}

    # Re-initialize client to ensure a fresh state for the GET request
    client = AireloomClient(
        settings=mock_settings_caching_enabled, base_url=MOCK_BASE_URL
    )
    httpx_mock.add_response(  # Add response for the new client instance's GET
        url=full_url, method="GET", status_code=200, json=get_mock_data
    )
    async with client:
        get_resp = await client.request("GET", url_path, expected_model=MockResource)
    assert get_resp == MockResource(**get_mock_data)
    assert len(httpx_mock.get_requests(url=full_url, method="GET")) == 1


# --- Hook System Tests ---


@pytest.mark.asyncio
async def test_client_pre_request_hook_called(
    httpx_mock: HTTPXMock, mock_settings: ApiSettings
):
    """Test that a single pre-request hook is called with correct arguments."""
    mock_pre_hook = MagicMock()
    settings = mock_settings.model_copy(update={"pre_request_hooks": [mock_pre_hook]})
    client = AireloomClient(settings=settings, base_url=MOCK_BASE_URL)

    request_url_path = "/hooktest_pre"
    full_request_url = f"{MOCK_BASE_URL}{request_url_path}"
    request_params = {"key": "value"}
    response_json = {"id": 1, "name": "Pre Hook Test"}

    httpx_mock.add_response(
        url=f"{full_request_url}?key=value",  # Match URL with params
        method="GET",
        json=response_json,
    )

    async with client:
        await client.request(
            "GET", request_url_path, params=request_params, expected_model=MockResource
        )

    mock_pre_hook.assert_called_once()
    args, _ = mock_pre_hook.call_args
    assert args[0] == "GET"  # method
    assert args[1] == full_request_url  # url
    assert args[2] == request_params  # params (should be a dict)
    assert isinstance(args[3], httpx.Headers)  # headers
    # User-Agent is set by the client after pre-request hooks if not already present.
    # With NoAuth, it won't be in headers passed to the hook unless a previous hook added it.
    # assert "User-Agent" not in args[3] # or check based on specific test conditions


@pytest.mark.asyncio
async def test_pre_request_hook_modifies_params_and_headers(
    httpx_mock: HTTPXMock, mock_settings: ApiSettings
):
    """Test that pre-request hooks can modify request parameters and headers."""
    original_params = {"param1": "original_value"}
    modified_params = {"param1": "modified_value", "param2": "added_value"}
    modified_headers_dict = {"X-Original-Header": "modified", "X-Added-Header": "added"}

    def modifying_pre_hook(method, url, params, headers):
        # Modify params
        if params is not None:
            params.clear()
            params.update(modified_params)
        # Modify headers
        headers.clear()  # Clear existing headers like User-Agent for predictable testing
        for k, v in modified_headers_dict.items():
            headers[k] = v
        headers["User-Agent"] = (
            "Hooked-User-Agent"  # Ensure User-Agent can be overridden
        )

    settings = mock_settings.model_copy(
        update={"pre_request_hooks": [modifying_pre_hook]}
    )
    client = AireloomClient(settings=settings, base_url=MOCK_BASE_URL)

    request_url_path = "/hook_modify_test"
    # The URL for httpx_mock should match the *modified* params
    # httpx_mock matches based on the final request sent
    final_request_url_with_params = (
        f"{MOCK_BASE_URL}{request_url_path}?param1=modified_value&param2=added_value"
    )

    httpx_mock.add_response(
        url=final_request_url_with_params,  # This needs to match the URL with modified params
        method="GET",
        json={"id": 1, "name": "Modified by Hook"},
    )

    async with client:
        await client.request(
            "GET",
            request_url_path,
            params=original_params.copy(),  # Pass a copy so original_params isn't modified by client setup
            expected_model=MockResource,
        )

    # Verify the request made to the server had modified params and headers
    made_requests = httpx_mock.get_requests()
    assert len(made_requests) == 1
    final_request = made_requests[0]

    # Check params (httpx.Request.url.params is an immutableQueryParams object)
    assert str(final_request.url) == final_request_url_with_params

    # Check headers
    for key, value in modified_headers_dict.items():
        assert final_request.headers[key] == value
    assert final_request.headers["User-Agent"] == "Hooked-User-Agent"


@pytest.mark.asyncio
async def test_client_post_request_hook_called(
    httpx_mock: HTTPXMock, mock_settings: ApiSettings
):
    """Test that a single post-request hook is called with response and parsed model."""
    mock_post_hook = MagicMock()
    settings = mock_settings.model_copy(update={"post_request_hooks": [mock_post_hook]})
    client = AireloomClient(settings=settings, base_url=MOCK_BASE_URL)

    request_url_path = "/hooktest_post"
    full_request_url = f"{MOCK_BASE_URL}{request_url_path}"
    response_json = {"id": 1, "name": "Post Hook Test", "value": 3.14}
    expected_parsed_model = MockResource(**response_json)

    httpx_mock.add_response(url=full_request_url, method="GET", json=response_json)

    async with client:
        parsed_model_result = await client.request(
            "GET", request_url_path, expected_model=MockResource
        )

    assert parsed_model_result == expected_parsed_model
    mock_post_hook.assert_called_once()
    args, _ = mock_post_hook.call_args
    assert isinstance(args[0], httpx.Response)  # raw httpx response
    assert args[0].status_code == 200
    assert args[0].json() == response_json
    assert args[1] == expected_parsed_model  # parsed pydantic model


@pytest.mark.asyncio
async def test_client_post_request_hook_model_parse_failure(
    httpx_mock: HTTPXMock, mock_settings: ApiSettings
):
    """Test post-request hook is called with None for model if parsing fails."""
    mock_post_hook = MagicMock()
    settings = mock_settings.model_copy(update={"post_request_hooks": [mock_post_hook]})
    client = AireloomClient(settings=settings, base_url=MOCK_BASE_URL)

    request_url_path = "/hooktest_post_fail"
    full_request_url = f"{MOCK_BASE_URL}{request_url_path}"
    # Response that will fail MockResource validation (e.g., missing 'name')
    response_json_malformed = {"id": 1, "val": 3.14}

    httpx_mock.add_response(
        url=full_request_url, method="GET", json=response_json_malformed
    )

    async with client:
        # Request will return raw response due to parsing failure
        raw_response = await client.request(
            "GET", request_url_path, expected_model=MockResource
        )

    assert isinstance(raw_response, httpx.Response)  # Should get raw response
    assert raw_response.json() == response_json_malformed

    mock_post_hook.assert_called_once()
    args, _ = mock_post_hook.call_args
    assert isinstance(args[0], httpx.Response)
    assert args[0].json() == response_json_malformed
    assert args[1] is None  # Parsed model should be None


@pytest.mark.asyncio
async def test_client_multiple_hooks_called(
    httpx_mock: HTTPXMock, mock_settings: ApiSettings
):
    """Test that multiple pre and post-request hooks are all called in order."""
    mock_pre_hook1 = MagicMock()
    mock_pre_hook2 = MagicMock()
    mock_post_hook1 = MagicMock()
    mock_post_hook2 = MagicMock()

    # Use a list to check call order
    call_order_recorder = []
    mock_pre_hook1.side_effect = lambda *args: call_order_recorder.append("pre1")
    mock_pre_hook2.side_effect = lambda *args: call_order_recorder.append("pre2")
    mock_post_hook1.side_effect = lambda *args: call_order_recorder.append("post1")
    mock_post_hook2.side_effect = lambda *args: call_order_recorder.append("post2")

    settings = mock_settings.model_copy(
        update={
            "pre_request_hooks": [mock_pre_hook1, mock_pre_hook2],
            "post_request_hooks": [mock_post_hook1, mock_post_hook2],
        }
    )
    client = AireloomClient(settings=settings, base_url=MOCK_BASE_URL)

    request_url_path = "/hooktest_multiple"
    full_request_url = f"{MOCK_BASE_URL}{request_url_path}"
    response_json = {"id": 1, "name": "Multiple Hooks"}

    httpx_mock.add_response(url=full_request_url, method="GET", json=response_json)

    async with client:
        await client.request("GET", request_url_path, expected_model=MockResource)

    mock_pre_hook1.assert_called_once()
    mock_pre_hook2.assert_called_once()
    mock_post_hook1.assert_called_once()
    mock_post_hook2.assert_called_once()

    assert call_order_recorder == ["pre1", "pre2", "post1", "post2"]


@pytest.mark.asyncio
async def test_client_no_hooks_works_correctly(
    httpx_mock: HTTPXMock, mock_settings: ApiSettings
):
    """Test client works correctly if no hooks are registered."""
    # Settings will have empty hook lists by default if not specified
    client = AireloomClient(settings=mock_settings, base_url=MOCK_BASE_URL)

    request_url_path = "/hooktest_none"
    full_request_url = f"{MOCK_BASE_URL}{request_url_path}"
    response_json = {"id": 1, "name": "No Hooks"}
    expected_model = MockResource(**response_json)

    httpx_mock.add_response(url=full_request_url, method="GET", json=response_json)

    async with client:
        result = await client.request(
            "GET", request_url_path, expected_model=MockResource
        )

    assert result == expected_model
    assert len(httpx_mock.get_requests()) == 1


@pytest.mark.asyncio
async def test_pre_request_hook_exception_does_not_stop_others_or_request(
    httpx_mock: HTTPXMock, mock_settings: ApiSettings
):
    """Test that an exception in one pre-request hook doesn't stop others or the main request."""
    mock_pre_hook_good1 = MagicMock()
    mock_pre_hook_bad = MagicMock(side_effect=ValueError("Pre-hook error"))
    mock_pre_hook_good2 = MagicMock()
    mock_post_hook = MagicMock()

    settings = mock_settings.model_copy(
        update={
            "pre_request_hooks": [
                mock_pre_hook_good1,
                mock_pre_hook_bad,
                mock_pre_hook_good2,
            ],
            "post_request_hooks": [mock_post_hook],
        }
    )
    client = AireloomClient(settings=settings, base_url=MOCK_BASE_URL)

    request_url_path = "/hook_exception_pre"
    full_request_url = f"{MOCK_BASE_URL}{request_url_path}"
    response_json = {"id": 1, "name": "Pre Hook Exception Test"}

    httpx_mock.add_response(url=full_request_url, method="GET", json=response_json)

    async with client:
        # The request should still succeed despite the hook error
        await client.request("GET", request_url_path, expected_model=MockResource)

    mock_pre_hook_good1.assert_called_once()
    mock_pre_hook_bad.assert_called_once()
    mock_pre_hook_good2.assert_called_once()  # Should still be called
    mock_post_hook.assert_called_once()  # Post hook should also be called
    assert len(httpx_mock.get_requests()) == 1  # Request should have been made


@pytest.mark.asyncio
async def test_post_request_hook_exception_does_not_stop_others(
    httpx_mock: HTTPXMock, mock_settings: ApiSettings
):
    """Test that an exception in one post-request hook doesn't stop others."""
    mock_post_hook_good1 = MagicMock()
    mock_post_hook_bad = MagicMock(side_effect=ValueError("Post-hook error"))
    mock_post_hook_good2 = MagicMock()

    settings = mock_settings.model_copy(
        update={
            "post_request_hooks": [
                mock_post_hook_good1,
                mock_post_hook_bad,
                mock_post_hook_good2,
            ]
        }
    )
    client = AireloomClient(settings=settings, base_url=MOCK_BASE_URL)

    request_url_path = "/hook_exception_post"
    full_request_url = f"{MOCK_BASE_URL}{request_url_path}"
    response_json = {"id": 1, "name": "Post Hook Exception Test"}

    httpx_mock.add_response(url=full_request_url, method="GET", json=response_json)

    async with client:
        # The request result should be unaffected by post-hook errors
        result = await client.request(
            "GET", request_url_path, expected_model=MockResource
        )

    assert result == MockResource(**response_json)
    mock_post_hook_good1.assert_called_once()
    mock_post_hook_bad.assert_called_once()
    mock_post_hook_good2.assert_called_once()  # Should still be called
    assert len(httpx_mock.get_requests()) == 1
