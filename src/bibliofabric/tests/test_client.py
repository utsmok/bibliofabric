"""Tests for the BaseApiClient in bibliofabric."""

import pytest
from unittest.mock import AsyncMock, MagicMock

import httpx

from bibliofabric.client import BaseApiClient
from bibliofabric.auth import NoAuth
from bibliofabric.models import ResponseUnwrapper
from bibliofabric.config import BaseApiSettings
from bibliofabric.exceptions import APIError, RateLimitError, TimeoutError


@pytest.fixture
def mock_unwrapper():
    """Fixture for a mock ResponseUnwrapper."""
    return MagicMock(spec=ResponseUnwrapper)


@pytest.fixture
def mock_settings():
    """Fixture for mock BaseApiSettings."""
    return BaseApiSettings(max_retries=3, backoff_factor=0.1)


@pytest.fixture
def base_api_client(mock_unwrapper, mock_settings):
    """Fixture for a BaseApiClient with a mock unwrapper."""
    return BaseApiClient(
        base_url="https://api.example.com",
        settings=mock_settings,
        response_unwrapper=mock_unwrapper,
        auth_strategy=NoAuth(),
    )


@pytest.mark.asyncio
async def test_request_with_retry_success(base_api_client: BaseApiClient, httpx_mock):
    """Test that _request_with_retry succeeds on the first attempt."""
    httpx_mock.add_response(status_code=200, json={"status": "ok"})

    response, _, attempts = await base_api_client._request_with_retry("GET", "/test")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert attempts == 1


@pytest.mark.asyncio
async def test_request_with_retry_failure_then_success(base_api_client: BaseApiClient, httpx_mock):
    """Test that _request_with_retry retries on 500 error and then succeeds."""
    httpx_mock.add_response(status_code=500, is_reusable=True)
    httpx_mock.add_response(status_code=200, json={"status": "ok"})

    response, _, attempts = await base_api_client._request_with_retry("GET", "/test")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert attempts == 2


@pytest.mark.asyncio
async def test_request_with_retry_all_failures(base_api_client: BaseApiClient, httpx_mock):
    """Test that _request_with_retry fails after all retries."""
    httpx_mock.add_response(status_code=500, is_reusable=True)

    with pytest.raises(APIError):
        await base_api_client._request_with_retry("GET", "/test")


@pytest.mark.asyncio
async def test_rate_limit_handling(base_api_client: BaseApiClient, httpx_mock):
    """Test that the client handles a 429 rate limit error."""
    httpx_mock.add_response(
        status_code=429, headers={"Retry-After": "1"}
    )
    httpx_mock.add_response(status_code=200, json={"status": "ok"})

    response, _, attempts = await base_api_client._request_with_retry("GET", "/test")

    assert response.status_code == 200
    assert attempts == 2


@pytest.mark.asyncio
async def test_timeout_error(base_api_client: BaseApiClient):
    """Test that a timeout raises an ApiError."""
    base_api_client._execute_single_request = AsyncMock(side_effect=[
        TimeoutError("Request timed out", request=httpx.Request("GET", "https://api.example.com/test")) for _ in range(base_api_client._settings.max_retries + 1)
    ])

    with pytest.raises(TimeoutError):
        await base_api_client._request_with_retry("GET", "/test")
