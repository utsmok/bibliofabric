"""Additional tests for client.py to cover error paths, caching, rate limiting, and hooks."""

from datetime import UTC, datetime as dt
from email.utils import formatdate
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import tenacity
from pydantic import BaseModel

from bibliofabric.auth import AuthStrategy
from bibliofabric.client import BaseApiClient
from bibliofabric.config import BaseApiSettings
from bibliofabric.exceptions import (
    APIError,
    AuthError,
    BibliofabricError,
    RateLimitError,
    TimeoutError,
)
from bibliofabric.models import ResponseUnwrapper
from bibliofabric.types import RequestData

# Constants for readability
HTTP_STATUS_OK = 200
HTTP_STATUS_BAD_REQUEST = 400
HTTP_STATUS_TOO_MANY = 429
HTTP_STATUS_SERVICE_UNAVAILABLE = 503
MD5_HEX_LENGTH = 32
RATE_LIMIT_CAPACITY = 100
RATE_LIMIT_LOW = 5
RATE_LIMIT_EXHAUSTED = 0
EXPECTED_SINGLE_REQUEST = 1
EXPECTED_TWO_REQUESTS = 2
EXPECTED_RETRY_AFTER = 30.0
EXPECTED_REMAINING = 50
EXPECTED_RESET_TIMESTAMP = 1700000000.0


# --- Shared fixtures ---


class SimpleModel(BaseModel):
    data: str


@pytest.fixture
def mock_unwrapper():
    return MagicMock(spec=ResponseUnwrapper)


@pytest.fixture
def mock_settings():
    return BaseApiSettings(
        max_retries=2,
        backoff_factor=0.01,
        enable_caching=True,
        cache_ttl_seconds=60,
        cache_max_size=100,
        enable_rate_limiting=True,
    )


@pytest.fixture
def base_client(mock_unwrapper, mock_settings):
    return BaseApiClient(
        settings=mock_settings,
        response_unwrapper=mock_unwrapper,
        base_url="https://api.example.com",
    )


# --- SSL fallback (lines 159-161) ---


@pytest.mark.asyncio
async def test_ssl_context_fallback_on_certifi_error(mock_unwrapper, mock_settings):
    """Test that client creation falls back when certifi fails."""
    mock_http_client = AsyncMock()
    mock_http_client.is_closed = False
    with (
        patch(
            "bibliofabric.client.certifi.where", side_effect=Exception("certifi fail")
        ),
        patch("bibliofabric.client.httpx.AsyncClient", return_value=mock_http_client),
    ):
        client = BaseApiClient(
            settings=mock_settings,
            response_unwrapper=mock_unwrapper,
            base_url="https://api.example.com",
        )
        assert client._http_client is mock_http_client
        await client.aclose()


# --- Rate limit header parsing (lines 186-246) ---


@pytest.mark.asyncio
async def test_parse_rate_limit_headers_all_headers(base_client):
    """Test parsing all rate limit headers including digit versions."""
    response = httpx.Response(
        HTTP_STATUS_OK,
        headers={
            "X-RateLimit-Limit": "100",
            "X-RateLimit-Remaining": "50",
            "X-RateLimit-Reset": "1700000000",
            "Retry-After": "30",
        },
        request=httpx.Request("GET", "https://api.example.com/test"),
    )
    result = await base_client._parse_rate_limit_headers(response)
    assert result == EXPECTED_RETRY_AFTER
    assert base_client._rate_limit_limit == RATE_LIMIT_CAPACITY
    assert base_client._rate_limit_remaining == EXPECTED_REMAINING
    assert base_client._rate_limit_reset_timestamp == EXPECTED_RESET_TIMESTAMP


@pytest.mark.asyncio
async def test_parse_rate_limit_headers_retry_after_http_date(base_client):
    """Test parsing Retry-After as HTTP date (lines 222-244)."""
    future_date = dt(2030, 1, 1, 0, 0, 0, tzinfo=UTC)
    http_date = formatdate(
        timeval=future_date.timestamp(),
        localtime=False,
        usegmt=True,
    )
    response = httpx.Response(
        HTTP_STATUS_OK,
        headers={"Retry-After": http_date},
        request=httpx.Request("GET", "https://api.example.com/test"),
    )
    result = await base_client._parse_rate_limit_headers(response)
    assert result is not None
    assert result >= 0


@pytest.mark.asyncio
async def test_parse_rate_limit_headers_retry_after_invalid_date(base_client):
    """Test Retry-After with invalid date string (lines 241-244)."""
    response = httpx.Response(
        HTTP_STATUS_OK,
        headers={"Retry-After": "not-a-valid-date"},
        request=httpx.Request("GET", "https://api.example.com/test"),
    )
    result = await base_client._parse_rate_limit_headers(response)
    assert result is None


@pytest.mark.asyncio
async def test_parse_rate_limit_headers_reset_http_date(base_client):
    """Test parsing X-RateLimit-Reset as HTTP date (lines 203-210)."""
    response = httpx.Response(
        HTTP_STATUS_OK,
        headers={"X-RateLimit-Reset": "Wed, 01 Jan 2030 00:00:00 GMT"},
        request=httpx.Request("GET", "https://api.example.com/test"),
    )
    await base_client._parse_rate_limit_headers(response)
    assert base_client._rate_limit_reset_timestamp is not None


@pytest.mark.asyncio
async def test_parse_rate_limit_headers_reset_invalid_date(base_client):
    """Test X-RateLimit-Reset with invalid date (lines 209-212)."""
    response = httpx.Response(
        HTTP_STATUS_OK,
        headers={"X-RateLimit-Reset": "not-a-date"},
        request=httpx.Request("GET", "https://api.example.com/test"),
    )
    await base_client._parse_rate_limit_headers(response)
    assert base_client._rate_limit_reset_timestamp is None


@pytest.mark.asyncio
async def test_parse_rate_limit_headers_non_digit_values(base_client):
    """Test that non-digit header values are skipped (lines 186-199 edge)."""
    response = httpx.Response(
        HTTP_STATUS_OK,
        headers={
            "X-RateLimit-Limit": "not-a-number",
            "X-RateLimit-Remaining": "also-not",
            "X-RateLimit-Reset": "nope",
        },
        request=httpx.Request("GET", "https://api.example.com/test"),
    )
    result = await base_client._parse_rate_limit_headers(response)
    assert result is None
    assert base_client._rate_limit_limit is None
    assert base_client._rate_limit_remaining is None


@pytest.mark.asyncio
async def test_parse_rate_limit_headers_generic_exception(base_client):
    """Test the outer exception handler (lines 245-246)."""
    response = MagicMock(spec=httpx.Response)
    response.headers = MagicMock()
    response.headers.get.side_effect = RuntimeError("unexpected error")
    result = await base_client._parse_rate_limit_headers(response)
    assert result is None


# --- Pre-request hook error (line 289-290) ---


@pytest.mark.asyncio
async def test_pre_request_hook_error_logged(base_client, httpx_mock):
    """Test that errors in pre-request hooks are logged but don't fail the request."""

    def bad_hook(method, url, params, headers):
        raise ValueError("hook failed")

    base_client._settings.pre_request_hooks = [bad_hook]
    httpx_mock.add_response(json={"data": "ok"}, status_code=HTTP_STATUS_OK)

    response, _parsed = await base_client._execute_single_request(
        RequestData(method="GET", url="https://api.example.com/test"),
        expected_model=SimpleModel,
    )
    assert response.status_code == HTTP_STATUS_OK


# --- Request body logging (line 316) ---


@pytest.mark.asyncio
async def test_request_body_logged_for_post(base_client, httpx_mock):
    """Test that request body is logged for POST requests (line 316)."""
    httpx_mock.add_response(json={"id": "1"}, status_code=HTTP_STATUS_OK)

    response, _parsed = await base_client._execute_single_request(
        RequestData(
            method="POST",
            url="https://api.example.com/test",
            json_data={"key": "value"},
        ),
    )
    assert response.status_code == HTTP_STATUS_OK


# --- Post-request hook error (lines 363-364) ---


@pytest.mark.asyncio
async def test_post_request_hook_error_logged(base_client, httpx_mock):
    """Test that errors in post-request hooks are logged but don't fail the request."""

    def bad_post_hook(response, parsed_model, attempts):
        raise ValueError("post hook failed")

    base_client._settings.post_request_hooks = [bad_post_hook]
    httpx_mock.add_response(json={"data": "ok"}, status_code=HTTP_STATUS_OK)

    response, _parsed = await base_client._execute_single_request(
        RequestData(method="GET", url="https://api.example.com/test"),
    )
    assert response.status_code == HTTP_STATUS_OK


# --- HTTPStatusError with 429 rate limit handling (lines 382-391) ---


@pytest.mark.asyncio
async def test_httpstatuserror_429_rate_limit(base_client):
    """Test httpx.HTTPStatusError with 429 triggers rate limit wait (lines 382-391)."""
    request = httpx.Request("GET", "https://api.example.com/test")
    error_response = httpx.Response(
        HTTP_STATUS_TOO_MANY, request=request, headers={"Retry-After": "1"}
    )

    base_client._http_client = AsyncMock(spec=httpx.AsyncClient)
    base_client._http_client.send = AsyncMock(
        side_effect=httpx.HTTPStatusError(
            "429", request=request, response=error_response
        )
    )

    with pytest.raises(RateLimitError):
        await base_client._execute_single_request(
            RequestData(method="GET", url="https://api.example.com/test"),
        )


# --- httpx.TimeoutException (lines 400-401) ---


@pytest.mark.asyncio
async def test_timeout_exception_raises_timeout_error(base_client):
    """Test httpx.TimeoutException is converted to TimeoutError (lines 400-401)."""
    base_client._http_client = AsyncMock(spec=httpx.AsyncClient)
    request = httpx.Request("GET", "https://api.example.com/test")
    base_client._http_client.send = AsyncMock(
        side_effect=httpx.TimeoutException("timeout", request=request)
    )

    with pytest.raises(TimeoutError):
        await base_client._execute_single_request(
            RequestData(method="GET", url="https://api.example.com/test"),
        )


# --- Generic exception in _execute_single_request (lines 412-426) ---


@pytest.mark.asyncio
async def test_unexpected_exception_during_request(base_client):
    """Test generic exception during request execution (lines 412-426)."""
    base_client._http_client = AsyncMock(spec=httpx.AsyncClient)
    base_client._http_client.send = AsyncMock(side_effect=RuntimeError("unexpected"))

    with pytest.raises(BibliofabricError, match="unexpected error"):
        await base_client._execute_single_request(
            RequestData(method="GET", url="https://api.example.com/test"),
        )


@pytest.mark.asyncio
async def test_bibliofabric_error_reraise_during_request(base_client):
    """Test that BibliofabricError subclasses are re-raised as-is (lines 420-421)."""
    request = httpx.Request("GET", "https://api.example.com/test")
    base_client._http_client = AsyncMock(spec=httpx.AsyncClient)
    base_client._http_client.send = AsyncMock(
        side_effect=APIError(
            "test error",
            response=httpx.Response(HTTP_STATUS_BAD_REQUEST, request=request),
        )
    )

    with pytest.raises(APIError):
        await base_client._execute_single_request(
            RequestData(method="GET", url="https://api.example.com/test"),
        )


# --- _should_retry_request (lines 439, 454-457, 464) ---


def test_should_retry_no_outcome(base_client):
    """Test _should_retry returns False when outcome is None (line 439)."""
    retry_state = MagicMock(spec=tenacity.RetryCallState)
    retry_state.outcome = None
    assert base_client._should_retry_request(retry_state) is False


def test_should_retry_httpx_timeout_exception(base_client):
    """Test _should_retry returns True for httpx.TimeoutException (lines 454-457)."""
    retry_state = MagicMock(spec=tenacity.RetryCallState)
    retry_state.outcome = MagicMock()
    retry_state.outcome.failed = True
    request = httpx.Request("GET", "https://api.example.com/test")
    retry_state.outcome.exception.return_value = httpx.TimeoutException(
        "timeout", request=request
    )
    assert base_client._should_retry_request(retry_state) is True


def test_should_retry_httpx_network_error(base_client):
    """Test _should_retry returns True for httpx.NetworkError (lines 454-457)."""
    retry_state = MagicMock(spec=tenacity.RetryCallState)
    retry_state.outcome = MagicMock()
    retry_state.outcome.failed = True
    request = httpx.Request("GET", "https://api.example.com/test")
    retry_state.outcome.exception.return_value = httpx.NetworkError(
        "connection", request=request
    )
    assert base_client._should_retry_request(retry_state) is True


def test_should_retry_httpx_http_status_error_retryable(base_client):
    """Test _should_retry returns True for retryable HTTPStatusError (line 464)."""
    retry_state = MagicMock(spec=tenacity.RetryCallState)
    retry_state.outcome = MagicMock()
    retry_state.outcome.failed = True
    request = httpx.Request("GET", "https://api.example.com/test")
    response = httpx.Response(HTTP_STATUS_SERVICE_UNAVAILABLE, request=request)
    retry_state.outcome.exception.return_value = httpx.HTTPStatusError(
        "503", request=request, response=response
    )
    assert base_client._should_retry_request(retry_state) is True


def test_should_retry_not_failed(base_client):
    """Test _should_retry returns False when outcome did not fail."""
    retry_state = MagicMock(spec=tenacity.RetryCallState)
    retry_state.outcome = MagicMock()
    retry_state.outcome.failed = False
    assert base_client._should_retry_request(retry_state) is False


# --- Pre-request rate limiting sleep (lines 523-547, 552-556) ---


@pytest.mark.asyncio
async def test_rate_limit_pre_request_wait_for_reset(base_client, httpx_mock):
    """Test that client waits when rate limit is approaching (lines 523-547)."""
    base_client._settings.enable_rate_limiting = True
    base_client._rate_limit_limit = RATE_LIMIT_CAPACITY
    base_client._rate_limit_remaining = RATE_LIMIT_LOW
    base_client._rate_limit_reset_timestamp = dt.now(UTC).timestamp() + 0.05

    httpx_mock.add_response(json={"data": "ok"}, status_code=HTTP_STATUS_OK)

    with patch(
        "bibliofabric.client.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        await base_client._request_with_retry("GET", "/test")
        mock_sleep.assert_called()


@pytest.mark.asyncio
async def test_rate_limit_pre_request_wait_default(base_client, httpx_mock):
    """Test client waits with default duration when reset_timestamp is None (lines 541-547)."""
    base_client._settings.enable_rate_limiting = True
    base_client._rate_limit_limit = RATE_LIMIT_CAPACITY
    base_client._rate_limit_remaining = RATE_LIMIT_EXHAUSTED
    base_client._rate_limit_reset_timestamp = None

    httpx_mock.add_response(json={"data": "ok"}, status_code=HTTP_STATUS_OK)

    with patch(
        "bibliofabric.client.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        await base_client._request_with_retry("GET", "/test")
        mock_sleep.assert_called_with(
            base_client._settings.rate_limit_retry_after_default
        )


@pytest.mark.asyncio
async def test_rate_limit_remaining_zero_no_limit_header(base_client, httpx_mock):
    """Test client waits when remaining=0 but limit is None (lines 550-556)."""
    base_client._settings.enable_rate_limiting = True
    base_client._rate_limit_remaining = RATE_LIMIT_EXHAUSTED
    base_client._rate_limit_limit = None

    httpx_mock.add_response(json={"data": "ok"}, status_code=HTTP_STATUS_OK)

    with patch(
        "bibliofabric.client.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        await base_client._request_with_retry("GET", "/test")
        mock_sleep.assert_called_with(
            base_client._settings.rate_limit_retry_after_default
        )


# --- Auth errors in _request_with_retry (lines 565-570) ---


@pytest.mark.asyncio
async def test_auth_error_in_request_with_retry(base_client):
    """Test AuthError propagation in _request_with_retry (line 565)."""
    base_client._auth_strategy = AsyncMock(spec=AuthStrategy)
    base_client._auth_strategy.async_authenticate = AsyncMock(
        side_effect=AuthError("auth fail")
    )

    with pytest.raises(AuthError, match="auth fail"):
        await base_client._request_with_retry("GET", "/test")


@pytest.mark.asyncio
async def test_unexpected_auth_error_in_request_with_retry(base_client):
    """Test unexpected exception during auth becomes BibliofabricError (lines 568-570)."""
    base_client._auth_strategy = AsyncMock(spec=AuthStrategy)
    base_client._auth_strategy.async_authenticate = AsyncMock(
        side_effect=RuntimeError("boom")
    )

    with pytest.raises(BibliofabricError, match="Unexpected authentication error"):
        await base_client._request_with_retry("GET", "/test")


# --- _before_retry_sleep (line 601) ---


@pytest.mark.asyncio
async def test_before_retry_sleep_no_outcome(base_client):
    """Test _before_retry_sleep with no outcome returns early (line 601)."""
    retry_state = MagicMock(spec=tenacity.RetryCallState)
    retry_state.outcome = None
    await base_client._before_retry_sleep(retry_state)


# --- Cache key generation with params (lines 643-644) ---


def test_generate_cache_key_with_params(base_client):
    """Test cache key generation includes params (lines 643-644)."""
    key1 = base_client._generate_cache_key(
        "GET", "https://api.example.com/test", {"a": 1, "b": 2}
    )
    key2 = base_client._generate_cache_key(
        "GET", "https://api.example.com/test", {"b": 2, "a": 1}
    )
    assert key1 == key2


def test_generate_cache_key_without_params(base_client):
    """Test cache key generation without params."""
    key = base_client._generate_cache_key("GET", "https://api.example.com/test")
    assert isinstance(key, str)
    assert len(key) == MD5_HEX_LENGTH


# --- Cache hit with type mismatch (lines 706-710) ---


@pytest.mark.asyncio
async def test_cache_hit_type_mismatch_discards_entry(base_client, httpx_mock):
    """Test that a cache hit with type mismatch is discarded (lines 706-710)."""
    cache_key = base_client._generate_cache_key("GET", "https://api.example.com/test")
    base_client._cache[cache_key] = {"wrong": "type"}

    httpx_mock.add_response(json={"data": "fresh"}, status_code=HTTP_STATUS_OK)

    result = await base_client.request("GET", "/test", expected_model=SimpleModel)
    assert isinstance(result, SimpleModel)
    assert result.data == "fresh"


# --- Cache store with None parsed_model (lines 747-750) ---


@pytest.mark.asyncio
async def test_cache_store_skipped_when_model_parsing_fails(base_client, httpx_mock):
    """Test that caching is skipped when model parsing fails (lines 747-750)."""
    httpx_mock.add_response(json={"wrong_field": "value"}, status_code=HTTP_STATUS_OK)

    result = await base_client.request("GET", "/test", expected_model=SimpleModel)
    assert isinstance(result, httpx.Response)


# --- aclose already closed client (line 786) ---


@pytest.mark.asyncio
async def test_aclose_already_closed_client(base_client):
    """Test aclose when HTTP client was already closed (line 786)."""
    await base_client._http_client.aclose()
    await base_client.aclose()


# --- 429 with rate limiting disabled ---


@pytest.mark.asyncio
async def test_429_rate_limiting_disabled(base_client, httpx_mock):
    """Test 429 handling when rate limiting is disabled."""
    base_client._settings.enable_rate_limiting = False
    httpx_mock.add_response(status_code=HTTP_STATUS_TOO_MANY)

    with pytest.raises(RateLimitError):
        await base_client._execute_single_request(
            RequestData(method="GET", url="https://api.example.com/test"),
        )


# --- Full request with cache miss then store ---


@pytest.mark.asyncio
async def test_request_cache_miss_then_store_and_hit(base_client, httpx_mock):
    """Test full request flow: cache miss -> fetch -> store -> cache hit."""
    httpx_mock.add_response(json={"data": "first"}, status_code=HTTP_STATUS_OK)

    result1 = await base_client.request(
        "GET", "/cached_endpoint", expected_model=SimpleModel
    )
    assert isinstance(result1, SimpleModel)
    assert result1.data == "first"

    result2 = await base_client.request(
        "GET", "/cached_endpoint", expected_model=SimpleModel
    )
    assert isinstance(result2, SimpleModel)
    assert result2.data == "first"
    assert len(httpx_mock.get_requests()) == EXPECTED_SINGLE_REQUEST


# --- Non-GET requests don't use cache ---


@pytest.mark.asyncio
async def test_post_request_not_cached(base_client, httpx_mock):
    """Test that POST requests are never cached."""
    httpx_mock.add_response(json={"data": "first"}, status_code=HTTP_STATUS_OK)
    httpx_mock.add_response(json={"data": "second"}, status_code=HTTP_STATUS_OK)

    r1 = await base_client.request(
        "POST", "/endpoint", json_data={"a": 1}, expected_model=SimpleModel
    )
    r2 = await base_client.request(
        "POST", "/endpoint", json_data={"a": 1}, expected_model=SimpleModel
    )

    assert r1.data == "first"
    assert r2.data == "second"
    assert len(httpx_mock.get_requests()) == EXPECTED_TWO_REQUESTS


# --- Retry-After naive date path (lines 230-233) ---


@pytest.mark.asyncio
async def test_parse_rate_limit_headers_retry_after_naive_http_date(base_client):
    """Test Retry-After with a naive date from parsedate_to_datetime (lines 230-233)."""
    naive_dt = dt(2030, 6, 1, 12, 0, 0)

    with patch("bibliofabric.client.parsedate_to_datetime", return_value=naive_dt):
        response = httpx.Response(
            HTTP_STATUS_OK,
            headers={"Retry-After": "Sun, 01 Jun 2030 12:00:00"},
            request=httpx.Request("GET", "https://api.example.com/test"),
        )
        result = await base_client._parse_rate_limit_headers(response)
        assert result is not None
        assert result >= 0


# --- Cache store type mismatch (line 743) ---


@pytest.mark.asyncio
async def test_cache_store_parsed_model_type_mismatch(base_client):
    """Test cache store when parsed_model doesn't match expected_model type (line 743)."""
    base_client._request_with_retry = AsyncMock(
        return_value=(
            httpx.Response(
                HTTP_STATUS_OK,
                json={"data": "ok"},
                request=httpx.Request("GET", "https://api.example.com/test"),
            ),
            {"data": "not_a_model"},
            1,
        )
    )

    result = await base_client.request("GET", "/test", expected_model=SimpleModel)
    assert isinstance(result, httpx.Response)
