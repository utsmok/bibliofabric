"""Tests for the BaseApiClient in bibliofabric."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from bibliofabric.auth import NoAuth
from bibliofabric.client import BaseApiClient
from bibliofabric.config import BaseApiSettings
from bibliofabric.exceptions import APIError, TimeoutError
from bibliofabric.models import ResponseUnwrapper


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
async def test_request_with_retry_failure_then_success(
    base_api_client: BaseApiClient, httpx_mock
):
    """Test that _request_with_retry retries on 500 error and then succeeds."""
    httpx_mock.add_response(status_code=500, is_reusable=True)
    httpx_mock.add_response(status_code=200, json={"status": "ok"})

    response, _, attempts = await base_api_client._request_with_retry("GET", "/test")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert attempts == 2


@pytest.mark.asyncio
async def test_request_with_retry_all_failures(
    base_api_client: BaseApiClient, httpx_mock
):
    """Test that _request_with_retry fails after all retries."""
    httpx_mock.add_response(status_code=500, is_reusable=True)

    with pytest.raises(APIError):
        await base_api_client._request_with_retry("GET", "/test")


@pytest.mark.asyncio
async def test_rate_limit_handling(base_api_client: BaseApiClient, httpx_mock):
    """Test that the client handles a 429 rate limit error."""
    httpx_mock.add_response(status_code=429, headers={"Retry-After": "1"})
    httpx_mock.add_response(status_code=200, json={"status": "ok"})

    response, _, attempts = await base_api_client._request_with_retry("GET", "/test")

    assert response.status_code == 200
    assert attempts == 2


@pytest.mark.asyncio
async def test_timeout_error(base_api_client: BaseApiClient):
    """Test that a timeout raises an ApiError."""
    base_api_client._execute_single_request = AsyncMock(
        side_effect=[
            TimeoutError(
                "Request timed out",
                request=httpx.Request("GET", "https://api.example.com/test"),
            )
            for _ in range(base_api_client._settings.max_retries + 1)
        ]
    )

    with pytest.raises(TimeoutError):
        await base_api_client._request_with_retry("GET", "/test")


@pytest.fixture
def base_api_client_with_mock_retry(mock_unwrapper, mock_settings):
    """Fixture for BaseApiClient where _request_with_retry is an AsyncMock."""
    client = BaseApiClient(
        base_url="https://api.example.com",
        settings=mock_settings,
        response_unwrapper=mock_unwrapper,
        auth_strategy=NoAuth(),
    )
    # Replace the real _request_with_retry with a mock for focused testing of .request()
    client._request_with_retry = AsyncMock()
    return client


@pytest.fixture
def base_api_client_with_cache(mock_unwrapper, mock_settings):
    """Fixture for BaseApiClient with caching enabled."""
    settings_with_cache = mock_settings.model_copy(
        update={"enable_caching": True, "cache_ttl_seconds": 300, "cache_max_size": 128}
    )

    client = BaseApiClient(
        base_url="https://api.example.com",
        settings=settings_with_cache,
        response_unwrapper=mock_unwrapper,
        auth_strategy=NoAuth(),
    )
    # Ensure cache is initialized
    assert client._cache is not None
    return client


@pytest.mark.asyncio
async def test_request_get_method_success_with_model(
    base_api_client_with_mock_retry, mock_unwrapper
):
    """Test .request() for GET with an expected Pydantic model."""

    class DummyModel(BaseModel):
        data: str

    mock_http_response = httpx.Response(
        200, json={"data": "success"}, request=httpx.Request("GET", "/test_model")
    )
    # _request_with_retry now returns (response, parsed_model, attempts)
    # For this test, assume parsing happens correctly within _request_with_retry or its mocks
    parsed_dummy_model = DummyModel(data="success")
    base_api_client_with_mock_retry._request_with_retry.return_value = (
        mock_http_response,
        parsed_dummy_model,
        1,
    )

    result = await base_api_client_with_mock_retry.request(
        "GET", "/test_model", expected_model=DummyModel
    )

    base_api_client_with_mock_retry._request_with_retry.assert_awaited_once_with(
        method="GET",
        path="/test_model",
        params=None,
        json_data=None,
        data=None,
        base_url_override=None,
        expected_model=DummyModel,
    )
    assert isinstance(result, DummyModel)
    assert result.data == "success"


@pytest.mark.asyncio
async def test_request_get_method_no_model(
    base_api_client_with_mock_retry, mock_unwrapper
):
    """Test .request() for GET without an expected model returns raw response."""
    mock_http_response = httpx.Response(
        200, json={"data": "raw_success"}, request=httpx.Request("GET", "/raw")
    )
    base_api_client_with_mock_retry._request_with_retry.return_value = (
        mock_http_response,
        None,
        1,
    )  # No parsed_model

    result = await base_api_client_with_mock_retry.request("GET", "/raw")

    base_api_client_with_mock_retry._request_with_retry.assert_awaited_once_with(
        method="GET",
        path="/raw",
        params=None,
        json_data=None,
        data=None,
        base_url_override=None,
        expected_model=None,
    )
    assert isinstance(result, httpx.Response)
    assert result.json() == {"data": "raw_success"}


@pytest.mark.asyncio
async def test_request_with_hooks(base_api_client_with_mock_retry):
    """Test that pre and post request hooks are called."""
    mock_pre_request_hook = MagicMock()  # Synchronous hook
    mock_post_request_hook = MagicMock()  # Synchronous hook

    # Use the standard base_api_client and mock its _http_client.send
    # to ensure _execute_single_request (where hooks are) is called.
    client = base_api_client_with_mock_retry  # Re-using fixture for settings, but will mock send
    client._settings.pre_request_hooks = [mock_pre_request_hook]
    client._settings.post_request_hooks = [mock_post_request_hook]

    mock_http_response = httpx.Response(
        200, json={"status": "ok"}, request=httpx.Request("GET", "/hook_test")
    )

    # Mock _http_client.send which is called by _execute_single_request
    # Also need to mock _auth_strategy.async_authenticate to avoid it trying to make real calls or raise errors
    client._http_client.send = AsyncMock(return_value=mock_http_response)
    client._auth_strategy.async_authenticate = AsyncMock()
    client._response_unwrapper.unwrap_results = MagicMock(
        return_value=[{"status": "ok"}]
    )  # if get_total_results etc. are called

    # Make _request_with_retry call the actual _execute_single_request by removing its mock
    # We need to re-assign the original method if it was mocked by the fixture, or use a different fixture.
    # For simplicity, let's ensure _request_with_retry is *not* the top-level mock for this test.
    # We will rely on tenacity to call _execute_single_request once.

    # To avoid tenacity's retry logic interfering with a simple hook test,
    # we can patch _execute_single_request directly for this one test,
    # but that defeats testing the hook call *within* _execute_single_request.
    # So, we let _request_with_retry run, which calls _execute_single_request.

    # Reset the mock for _request_with_retry if the fixture set one up.
    # The fixture base_api_client_with_mock_retry specifically mocks _request_with_retry.
    # We need a client where _request_with_retry is *not* mocked for this test.

    # Let's use a new client instance or modify the existing one carefully.
    # The easiest is to re-patch _request_with_retry to call the original,
    # or better, use a fixture that doesn't mock _request_with_retry.
    # For now, let's assume the fixture `base_api_client` can be used if its send is mocked.

    # Using the `base_api_client` fixture which doesn't mock _request_with_retry

    # Re-configure client from a more basic fixture if needed, or ensure this one's state is fine.
    # The issue is that base_api_client_with_mock_retry *by definition* mocks _request_with_retry.
    # We need to test the actual _request_with_retry's call to _execute_single_request.

    # Let's redefine what base_api_client_with_mock_retry means for this test.
    # We will mock _execute_single_request itself for other tests, but for testing hooks inside it,
    # we need it to run.

    # Correct approach: Mock what _execute_single_request calls internally, i.e., _http_client.send
    # The fixture `base_api_client_with_mock_retry` already has _request_with_retry as an AsyncMock.
    # This test should test the `request()` method's interaction with `_request_with_retry`
    # and `_request_with_retry`'s interaction with `_execute_single_request` for hooks.
    # So, `_request_with_retry` should call `_execute_single_request`.
    # The `base_api_client_with_mock_retry` fixture mocks `_request_with_retry` itself,
    # which means `_execute_single_request` (where hooks are) is never called.

    # We need a client where _request_with_retry is the *real* method.
    # We can achieve this by creating a fresh client or using the `base_api_client` fixture
    # and then mocking its `_http_client.send`.

    settings = client._settings  # use settings from the fixture
    unwrapper = client._response_unwrapper  # use unwrapper from the fixture

    fresh_client = BaseApiClient(
        base_url="https://api.example.com",
        settings=settings,
        response_unwrapper=unwrapper,
        auth_strategy=NoAuth(),  # Using NoAuth for simplicity here
    )
    fresh_client._settings.pre_request_hooks = [mock_pre_request_hook]
    fresh_client._settings.post_request_hooks = [mock_post_request_hook]
    fresh_client._http_client.send = AsyncMock(
        return_value=mock_http_response
    )  # Mock send

    await fresh_client.request("GET", "/hook_test", expected_model=dict)

    mock_pre_request_hook.assert_called_once()
    # Pre-hook gets method, url, params, data, json_data, headers
    pre_args, _ = mock_pre_request_hook.call_args
    # Pre-hook gets method, url, params, headers (original RequestData content)
    pre_args, _ = mock_pre_request_hook.call_args
    assert pre_args[0] == "GET"  # method
    assert pre_args[1] == "https://api.example.com/hook_test"  # url
    # pre_args[2] is params, pre_args[3] is headers

    mock_post_request_hook.assert_called_once()
    # Post-hook gets response, parsed_model, attempts
    post_args, _ = mock_post_request_hook.call_args
    assert post_args[0] == mock_http_response  # response
    assert (
        post_args[1] is None
    )  # parsed_model will be None as dict.model_validate fails
    assert post_args[2] == 1  # attempts


@pytest.mark.asyncio
async def test_request_post_method(base_api_client_with_mock_retry, mock_unwrapper):
    """Test making a POST request."""
    mock_http_response = httpx.Response(
        200,
        json={"id": "1", "status": "created"},
        request=httpx.Request("POST", "/test"),
    )
    base_api_client_with_mock_retry._request_with_retry = AsyncMock(
        return_value=(mock_http_response, {"id": "1"}, 1)
    )

    json_payload = {"data": "test_payload"}
    response = await base_api_client_with_mock_retry.request(
        "POST", "/test", json_data=json_payload, expected_model=dict
    )

    base_api_client_with_mock_retry._request_with_retry.assert_awaited_once_with(
        method="POST",
        path="/test",
        params=None,
        json_data=json_payload,
        data=None,
        base_url_override=None,
        expected_model=dict,
    )
    assert response == {"id": "1"}


@pytest.mark.asyncio
async def test_request_put_method(base_api_client_with_mock_retry, mock_unwrapper):
    """Test making a PUT request."""
    mock_http_response = httpx.Response(
        200,
        json={"id": "1", "status": "updated"},
        request=httpx.Request("PUT", "/test/1"),
    )
    base_api_client_with_mock_retry._request_with_retry = AsyncMock(
        return_value=(mock_http_response, {"id": "1"}, 1)
    )

    json_payload = {"data": "updated_payload"}
    response = await base_api_client_with_mock_retry.request(
        "PUT", "/test/1", json_data=json_payload, expected_model=dict
    )

    base_api_client_with_mock_retry._request_with_retry.assert_awaited_once_with(
        method="PUT",
        path="/test/1",
        params=None,
        json_data=json_payload,
        data=None,
        base_url_override=None,
        expected_model=dict,
    )
    assert response == {"id": "1"}


@pytest.mark.asyncio
async def test_request_delete_method(base_api_client_with_mock_retry, mock_unwrapper):
    """Test making a DELETE request."""
    mock_http_response = httpx.Response(
        204, request=httpx.Request("DELETE", "/test/1")
    )  # No JSON body for 204
    base_api_client_with_mock_retry._request_with_retry = AsyncMock(
        return_value=(mock_http_response, None, 1)
    )

    response = await base_api_client_with_mock_retry.request("DELETE", "/test/1")

    base_api_client_with_mock_retry._request_with_retry.assert_awaited_once_with(
        method="DELETE",
        path="/test/1",
        params=None,
        json_data=None,
        data=None,
        base_url_override=None,
        expected_model=None,
    )
    assert isinstance(
        response, httpx.Response
    )  # Should return raw response if no model
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_caching_get_request_cache_miss_and_hit(
    base_api_client_with_cache, mock_unwrapper
):
    """Test caching for GET requests: first call is a miss, second is a hit."""

    class SimpleModel(BaseModel):
        key: str

    mock_http_response = httpx.Response(
        200, json={"key": "value"}, request=httpx.Request("GET", "/cache_test")
    )

    # Mock _request_with_retry to be called only once (for cache miss)
    base_api_client_with_cache._request_with_retry = AsyncMock(
        return_value=(mock_http_response, SimpleModel(key="value"), 1)
    )
    base_api_client_with_cache._unwrapper = mock_unwrapper  # Ensure unwrapper is set

    # First call (cache miss)
    result1 = await base_api_client_with_cache.request(
        "GET", "/cache_test", expected_model=SimpleModel
    )
    assert isinstance(result1, SimpleModel)
    assert result1.key == "value"
    base_api_client_with_cache._request_with_retry.assert_awaited_once()

    # Second call (should be cache hit)
    result2 = await base_api_client_with_cache.request(
        "GET", "/cache_test", expected_model=SimpleModel
    )
    assert isinstance(result2, SimpleModel)
    assert result2.key == "value"
    # _request_with_retry should still only have been called once
    base_api_client_with_cache._request_with_retry.assert_awaited_once()


@pytest.mark.asyncio
async def test_caching_disabled_for_non_get_requests(
    base_api_client_with_cache, mock_unwrapper
):
    """Test that caching is not applied for non-GET requests."""

    class SimpleModel(BaseModel):
        key: str

    mock_http_response = httpx.Response(
        200,
        json={"key": "value_post"},
        request=httpx.Request("POST", "/cache_test_post"),
    )

    base_api_client_with_cache._request_with_retry = AsyncMock(
        return_value=(mock_http_response, SimpleModel(key="value_post"), 1)
    )
    base_api_client_with_cache._unwrapper = mock_unwrapper

    # First POST call
    await base_api_client_with_cache.request(
        "POST",
        "/cache_test_post",
        json_data={"data": "payload"},
        expected_model=SimpleModel,
    )
    assert base_api_client_with_cache._request_with_retry.call_count == 1

    # Second POST call (should not hit cache)
    await base_api_client_with_cache.request(
        "POST",
        "/cache_test_post",
        json_data={"data": "payload"},
        expected_model=SimpleModel,
    )
    assert base_api_client_with_cache._request_with_retry.call_count == 2


@pytest.mark.asyncio
async def test_request_with_retry_handles_httpx_request_error(
    base_api_client, mock_unwrapper
):
    """Test _request_with_retry handles httpx.NetworkError and raises NetworkError."""
    # Use httpx.NetworkError for this test path
    base_api_client._http_client.send = AsyncMock(
        side_effect=httpx.NetworkError(
            "DNS resolution failed", request=httpx.Request("GET", "/test")
        )
    )
    base_api_client._auth_strategy.async_authenticate = AsyncMock()
    base_api_client._unwrapper = mock_unwrapper

    with pytest.raises(
        NetworkError,
        match="Network error for https://api.example.com/test: DNS resolution failed",
    ):
        await base_api_client._request_with_retry("GET", "/test")


@pytest.mark.asyncio
async def test_request_with_retry_handles_generic_httpx_request_error(
    base_api_client, mock_unwrapper
):
    """Test _request_with_retry handles generic httpx.RequestError and raises BibliofabricRequestError."""

    # Use a generic httpx.RequestError that is not a NetworkError or TimeoutException
    class OtherRequestError(httpx.RequestError):
        pass

    base_api_client._http_client.send = AsyncMock(
        side_effect=OtherRequestError(
            "Some other request error", request=httpx.Request("GET", "/test")
        )
    )
    base_api_client._auth_strategy.async_authenticate = AsyncMock()
    base_api_client._unwrapper = mock_unwrapper

    with pytest.raises(
        BibliofabricRequestError,
        match="HTTP request error for https://api.example.com/test: Some other request error",
    ):
        await base_api_client._request_with_retry("GET", "/test")


@pytest.mark.asyncio
async def test_request_with_retry_handles_httpx_http_status_error(
    base_api_client, mock_unwrapper
):
    """Test _request_with_retry handles httpx.HTTPStatusError and raises BibliofabricRequestError."""
    mock_http_response = httpx.Response(
        500, text="Server Error", request=httpx.Request("GET", "/test")
    )
    base_api_client._http_client.send = AsyncMock(
        side_effect=httpx.HTTPStatusError(
            "Server Error",
            request=httpx.Request("GET", "/test"),
            response=mock_http_response,
        )
    )
    base_api_client._auth_strategy.async_authenticate = AsyncMock()
    base_api_client._unwrapper = mock_unwrapper

    with pytest.raises(
        APIError, match="API request failed with status 500"
    ):  # Match changed to APIError
        await base_api_client._request_with_retry("GET", "/test")


@pytest.mark.asyncio
async def test_request_with_auth_failure(base_api_client):
    """Test that AuthError during authentication attempt is propagated."""
    base_api_client._auth_strategy.async_authenticate = AsyncMock(
        side_effect=AuthError("Token expired")
    )

    with pytest.raises(AuthError, match="Token expired"):
        await base_api_client._request_with_retry("GET", "/auth_fail_test")


@pytest.mark.asyncio
async def test_aclose_closes_internal_http_client(base_api_client):
    """Test that aclose() closes the internal HTTP client if it was created by BaseApiClient."""
    # Ensure an internal client exists and is open
    assert base_api_client._http_client is not None
    assert not base_api_client._http_client.is_closed

    await base_api_client.aclose()
    assert base_api_client._http_client.is_closed


@pytest.mark.asyncio
async def test_aclose_does_not_close_external_http_client():
    """Test that aclose() does not close an externally provided HTTP client."""
    external_client = httpx.AsyncClient()
    settings = BaseApiSettings()  # Default settings
    unwrapper = MagicMock(spec=ResponseUnwrapper)

    client_with_external_http = BaseApiClient(
        base_url="http://example.com",
        settings=settings,
        response_unwrapper=unwrapper,
        http_client=external_client,  # Pass external client
    )
    assert not external_client.is_closed
    await client_with_external_http.aclose()
    assert not external_client.is_closed  # External client should remain open
    await external_client.aclose()  # Clean up external client


@pytest.mark.asyncio
async def test_client_as_context_manager(mock_unwrapper):
    """Test BaseApiClient as an asynchronous context manager."""
    settings = BaseApiSettings()
    async with BaseApiClient(
        base_url="http://example.com",
        settings=settings,
        response_unwrapper=mock_unwrapper,
    ) as client:
        assert client._http_client is not None
        assert not client._http_client.is_closed
    assert client._http_client.is_closed  # Should be closed upon exiting context


@pytest.mark.asyncio
async def test_request_with_base_url_override(
    base_api_client_with_mock_retry, mock_unwrapper
):
    """Test that base_url_override is correctly used in requests."""
    mock_http_response = httpx.Response(
        200,
        json={"data": "override_success"},
        request=httpx.Request("GET", "https://override.example.com/test"),
    )
    base_api_client_with_mock_retry._request_with_retry.return_value = (
        mock_http_response,
        {"data": "override_success"},
        1,
    )

    await base_api_client_with_mock_retry.request(
        "GET",
        "/test",
        base_url_override="https://override.example.com",
        expected_model=dict,
    )

    args, kwargs = base_api_client_with_mock_retry._request_with_retry.call_args
    assert kwargs["base_url_override"] == "https://override.example.com"
    # The RequestData object passed to _request_with_retry will have the full overridden URL
    # This can be checked if _request_with_retry's input `request_data.url` is inspected,
    # but for now, checking the kwarg passed to it is sufficient.


@pytest.mark.asyncio
async def test_request_json_alias_for_json_data(
    base_api_client_with_mock_retry, mock_unwrapper
):
    """Test that the 'json' alias for 'json_data' works correctly."""
    mock_http_response = httpx.Response(
        200, json={"status": "created"}, request=httpx.Request("POST", "/alias_test")
    )
    base_api_client_with_mock_retry._request_with_retry.return_value = (
        mock_http_response,
        {"status": "created"},
        1,
    )

    payload = {"key": "value"}
    # Use the 'json' alias
    await base_api_client_with_mock_retry.request(
        "POST", "/alias_test", json=payload, expected_model=dict
    )

    args, kwargs = base_api_client_with_mock_retry._request_with_retry.call_args
    assert (
        kwargs["json_data"] == payload
    )  # Internally, it should be passed as json_data
    # The 'json' key should not be present in the kwargs passed to _request_with_retry
    # if json_data was derived from it.
    assert "json" not in kwargs or kwargs["json"] is None


from io import StringIO

from bibliofabric.log_config import (
    logger as bibliofabric_logger,  # Import the specific logger
)


@pytest.mark.asyncio
async def test_request_both_json_and_json_data_uses_json_data(
    base_api_client_with_mock_retry, mock_unwrapper
):
    """Test that if both 'json' and 'json_data' are provided, 'json_data' is used and a warning is logged."""
    mock_http_response = httpx.Response(
        200, json={"status": "ok"}, request=httpx.Request("POST", "/conflict_test")
    )
    base_api_client_with_mock_retry._request_with_retry.return_value = (
        mock_http_response,
        {"status": "ok"},
        1,
    )

    json_payload = {"alias": "value"}
    json_data_payload = {"actual": "value_from_json_data"}

    # Capture loguru output for this test
    log_capture_string = StringIO()
    original_handlers = list(bibliofabric_logger._core.handlers.keys())
    bibliofabric_logger.remove()  # Remove existing handlers
    # Add a handler that writes to our StringIO, ensure it captures warnings
    handler_id = bibliofabric_logger.add(
        log_capture_string, level="WARNING", format="{message}"
    )

    await base_api_client_with_mock_retry.request(
        "POST",
        "/conflict_test",
        json=json_payload,
        json_data=json_data_payload,
        expected_model=dict,
    )

    args, kwargs = base_api_client_with_mock_retry._request_with_retry.call_args
    assert kwargs["json_data"] == json_data_payload  # json_data should take precedence

    logged_text = log_capture_string.getvalue()
    assert (
        "Both 'json' and 'json_data' provided to request; using 'json_data'."
        in logged_text
    )

    # Restore original logger handlers
    bibliofabric_logger.remove(handler_id)
    # This part is tricky; ideally, we'd restore exactly the previous handlers.
    # For now, let's re-add a default stderr handler if no other handlers were there.
    # A more robust solution might involve a fixture to manage logger state.
    if (
        not bibliofabric_logger._core.handlers
    ):  # if it's empty after removing our test handler
        from bibliofabric.log_config import (
            configure_logging as bfl_configure_logging,  # avoid name clash
        )

        bfl_configure_logging()  # Re-apply default config


from pydantic import BaseModel

from bibliofabric.exceptions import AuthError, BibliofabricRequestError, NetworkError
