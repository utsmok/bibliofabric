"""Generic API client implementation for the bibliofabric framework.

This module provides the BaseApiClient class, which contains all the generic
HTTP client logic needed to build robust, asynchronous API clients. It handles
retries, caching, rate limiting, authentication, and error handling in a
completely API-agnostic way through the ResponseUnwrapper protocol.
"""

import asyncio
import hashlib
import json
import ssl
import time
from collections.abc import Mapping
from datetime import UTC, datetime as dt
from email.utils import parsedate_to_datetime
from http import HTTPStatus
from typing import Any, Self

import certifi
import httpx
import tenacity
from cachetools import TTLCache  # type: ignore[import-untyped]
from tenacity import (
    AsyncRetrying,
    stop_after_attempt,
    wait_exponential,
)

from .auth import AuthStrategy, NoAuth
from .config import BaseApiSettings
from .exceptions import (
    APIError,
    AuthError,
    BibliofabricError,
    BibliofabricRequestError,  # Added import
    NetworkError,
    RateLimitError,
    TimeoutError,
)
from .log_config import logger
from .models import ResponseUnwrapper
from .types import RequestData


class BaseApiClient:
    """Generic asynchronous HTTP client for interacting with APIs.

    This class provides a robust foundation for building API clients with built-in
    support for retries, caching, rate limiting, authentication, and error handling.
    It uses the ResponseUnwrapper protocol to enable API-agnostic response processing.

    The client is designed to be inherited by specific API implementations that
    provide their own ResponseUnwrapper and configure API-specific settings like
    base URLs and authentication strategies.

    Key features:
    - Automatic retries with exponential backoff for transient errors
    - Client-side caching for GET requests with configurable TTL
    - Rate limit detection and automatic throttling
    - Pluggable authentication strategies
    - Comprehensive error handling and logging
    - Pre/post request hooks for customization
    - Response unwrapping through the ResponseUnwrapper protocol

    Attributes:
        _settings: Configuration settings for the client.
        _response_unwrapper: Instance to handle API-specific response structures.
        _base_url: The base URL for API requests.
        _retryable_status_codes: HTTP status codes that trigger a retry.
        _cache: Optional TTL cache for GET requests.
        _auth_strategy: Authentication strategy instance.
        _http_client: The underlying httpx.AsyncClient for making requests.
        _should_close_client: Flag indicating if this instance owns the _http_client.
        _rate_limit_limit: Last observed rate limit capacity.
        _rate_limit_remaining: Last observed remaining requests in the current window.
        _rate_limit_reset_timestamp: Timestamp for when the rate limit window resets.
        _rate_limit_lock: Lock for synchronizing access to rate limit state.
    """

    DEFAULT_RETRYABLE_STATUS_CODES: frozenset[int] = frozenset(
        [429, 500, 502, 503, 504]
    )
    """Default set of HTTP status codes considered retryable."""

    def __init__(
        self,
        settings: BaseApiSettings,
        response_unwrapper: ResponseUnwrapper,
        auth_strategy: AuthStrategy | None = None,
        *,
        base_url: str,
        http_client: httpx.AsyncClient | None = None,
        retryable_status_codes: frozenset[int] = DEFAULT_RETRYABLE_STATUS_CODES,
    ):
        """Initialize the BaseApiClient.

        Args:
            settings: Configuration settings for the API client behavior.
            response_unwrapper: Protocol implementation for handling API-specific
                response structures and pagination.
            auth_strategy: Optional authentication strategy. If None, uses NoAuth.
            base_url: The base URL for API requests.
            http_client: Optional pre-configured httpx.AsyncClient instance.
            retryable_status_codes: Set of HTTP status codes to retry on.

        Note:
            The base_url should be provided by the specific API client implementation
            and not hardcoded here to maintain the generic nature of this class.
        """
        self._settings = settings
        self._response_unwrapper = response_unwrapper
        self._base_url: str = base_url.rstrip("/")
        self._retryable_status_codes: frozenset[int] = retryable_status_codes

        # Initialize cache
        self._cache: TTLCache[str, Any] | None = None
        if self._settings.enable_caching and self._settings.cache_ttl_seconds > 0:
            logger.info(
                f"Client-side caching enabled. Max size: {self._settings.cache_max_size}, "
                f"TTL: {self._settings.cache_ttl_seconds}s"
            )
            self._cache = TTLCache(  # type: ignore[type-arg]
                maxsize=self._settings.cache_max_size,
                ttl=self._settings.cache_ttl_seconds,
            )
        else:
            logger.info("Client-side caching is disabled.")

        # Set up authentication strategy
        self._auth_strategy: AuthStrategy = auth_strategy or NoAuth()
        logger.info(
            f"Using authentication strategy: {type(self._auth_strategy).__name__}"
        )

        # HTTP client setup
        self._should_close_client = http_client is None  # Close only if we created it
        self._http_client = http_client or self._create_default_http_client()

        # Rate limiting state
        self._rate_limit_limit: int | None = None
        self._rate_limit_remaining: int | None = None
        self._rate_limit_reset_timestamp: float | None = None  # Unix timestamp
        self._rate_limit_lock = asyncio.Lock()

        logger.debug("BaseApiClient initialized.")

    def _create_default_http_client(self) -> httpx.AsyncClient:
        """Create a default httpx.AsyncClient with configured settings.

        Returns:
            httpx.AsyncClient: Configured HTTP client with SSL verification,
                timeout settings, and user agent header.
        """
        try:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            verify_ssl = ssl_context
            logger.debug("Using certifi SSL context.")
        except Exception:
            verify_ssl = True
            logger.warning(
                "certifi not found or failed to load. Using default SSL verification."
            )

        return httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._settings.request_timeout,
            verify=verify_ssl,
            headers={"User-Agent": self._settings.user_agent},
        )

    async def _parse_rate_limit_headers(self, response: httpx.Response) -> float | None:
        """Parse rate limit headers from the response and update client state.

        Args:
            response: The HTTP response to parse headers from.

        Returns:
            float | None: The 'Retry-After' duration in seconds, if present.
        """
        retry_after_seconds: float | None = None
        async with self._rate_limit_lock:
            try:
                limit_str = response.headers.get("X-RateLimit-Limit")
                if limit_str and limit_str.isdigit():
                    self._rate_limit_limit = int(limit_str)
                    logger.debug(f"Parsed X-RateLimit-Limit: {self._rate_limit_limit}")

                remaining_str = response.headers.get("X-RateLimit-Remaining")
                if remaining_str and remaining_str.isdigit():
                    self._rate_limit_remaining = int(remaining_str)
                    logger.debug(
                        f"Parsed X-RateLimit-Remaining: {self._rate_limit_remaining}"
                    )

                reset_str = response.headers.get("X-RateLimit-Reset")
                if reset_str and reset_str.isdigit():
                    self._rate_limit_reset_timestamp = float(reset_str)
                    logger.debug(
                        f"Parsed X-RateLimit-Reset: {self._rate_limit_reset_timestamp}"
                    )
                elif reset_str:  # Could be an HTTP date
                    try:
                        dt_reset_obj = parsedate_to_datetime(reset_str)
                        self._rate_limit_reset_timestamp = dt_reset_obj.timestamp()
                        logger.debug(
                            f"Parsed X-RateLimit-Reset (HTTP date): {self._rate_limit_reset_timestamp}"
                        )
                    except Exception:
                        logger.warning(
                            f"Could not parse X-RateLimit-Reset HTTP date: {reset_str}"
                        )

                retry_after_header = response.headers.get("Retry-After")
                if retry_after_header:
                    if retry_after_header.isdigit():
                        retry_after_seconds = float(retry_after_header)
                        logger.debug(
                            f"Parsed Retry-After (seconds): {retry_after_seconds}"
                        )
                    else:
                        try:
                            # Attempt to parse as HTTP-date
                            retry_dt_obj = parsedate_to_datetime(retry_after_header)
                            # Ensure it's timezone-aware for correct comparison
                            if (
                                retry_dt_obj.tzinfo is None
                                or retry_dt_obj.tzinfo.utcoffset(retry_dt_obj) is None
                            ):
                                logger.warning(
                                    f"Retry-After date '{retry_after_header}' is naive, assuming UTC."
                                )
                                retry_dt_obj = retry_dt_obj.replace(tzinfo=UTC)

                            now_dt_obj = dt.now(UTC)
                            delta = retry_dt_obj - now_dt_obj
                            retry_after_seconds = max(0, delta.total_seconds())
                            logger.debug(
                                f"Parsed Retry-After (HTTP date): {retry_after_header}, calculated seconds: {retry_after_seconds}"
                            )
                        except Exception as e:
                            logger.warning(
                                f"Could not parse Retry-After HTTP date '{retry_after_header}': {e}"
                            )
            except Exception as e:
                logger.exception(f"Error parsing rate limit headers: {e}")
        return retry_after_seconds

    async def _execute_single_request(
        self, request_data: RequestData, expected_model: type[Any] | None = None
    ) -> tuple[httpx.Response, Any | None]:
        """Execute a single HTTP request attempt, run hooks, and parse if model provided.

        Args:
            request_data: The request data including method, URL, params, etc.
            expected_model: Optional Pydantic model class for response validation.

        Returns:
            tuple[httpx.Response, Any | None]: The HTTP response and optionally
                parsed model instance if expected_model was provided and parsing succeeded.

        Raises:
            RateLimitError: If API rate limit is exceeded (429 status).
            APIError: For other HTTP error responses (4xx/5xx).
            TimeoutError: If the request times out.
            NetworkError: For network-related errors.
            BibliofabricError: For other unexpected errors.
        """
        # --- Pre-Request Hooks ---
        # Prepare mutable versions of params and headers for hooks
        hook_params: dict[str, Any] | None = (
            dict(request_data.params) if request_data.params is not None else None
        )
        hook_headers: httpx.Headers = httpx.Headers(request_data.headers)

        if self._settings.pre_request_hooks:
            logger.debug(
                f"Executing {len(self._settings.pre_request_hooks)} pre-request hooks "
                f"for {request_data.method} {request_data.url}"
            )
            for hook in self._settings.pre_request_hooks:
                try:
                    hook(
                        request_data.method,
                        request_data.url,
                        hook_params,
                        hook_headers,
                    )
                except Exception as e:
                    logger.error(
                        f"Error executing pre-request hook {getattr(hook, '__name__', str(hook))}: {e}",
                        exc_info=True,
                    )

            # Update request_data from potentially modified hook_params and hook_headers
            request_data.params = hook_params
            # Convert modified hook_headers (httpx.Headers) back to a dict for request_data.headers
            request_data.headers = {k: v for k, v in hook_headers.items()}

        request = request_data.build_request()
        response: httpx.Response | None = None
        parsed_model: Any | None = None
        retry_after_from_headers: float | None = None

        try:
            # Apply authentication just before sending
            await self._auth_strategy.async_authenticate(request)

            # Ensure User-Agent is set
            if "User-Agent" not in request.headers or not request.headers["User-Agent"]:
                request.headers["User-Agent"] = self._settings.user_agent

            logger.debug(f"Sending request: {request.method} {request.url}")
            logger.trace(f"Request Headers: {request.headers}")
            if request.content:
                logger.trace(f"Request Body: {request.content.decode()}")

            response = await self._http_client.send(request)
            retry_after_from_headers = await self._parse_rate_limit_headers(response)

            logger.debug(f"Received response: {response.status_code} for {request.url}")
            logger.trace(f"Response Headers: {response.headers}")

            if response.status_code >= HTTPStatus.BAD_REQUEST:
                if response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                    if self._settings.enable_rate_limiting:
                        wait_duration = (
                            retry_after_from_headers
                            or self._settings.rate_limit_retry_after_default
                        )
                        logger.info(
                            f"Rate limit hit (429). Raising RateLimitError. Retry will be handled by tenacity with appropriate wait. Wait duration hint from server: {wait_duration:.2f}s. Client open: {not self._http_client.is_closed if self._http_client else 'N/A'}"
                        )
                    logger.error(
                        f"Raising RateLimitError after 429. Client open: {not self._http_client.is_closed if self._http_client else 'N/A'}"
                    )
                    raise RateLimitError("API rate limit exceeded.", response=response)
                raise APIError(
                    f"API request failed with status {response.status_code}",
                    response=response,
                )

            # Successful response, try parsing if expected_model is provided
            if expected_model:
                try:
                    parsed_model = expected_model.model_validate(response.json())
                except Exception as e:
                    logger.warning(
                        f"Response model validation failed for {request.url}: {e}. "
                        "Parsed model will be None."
                    )
                    # parsed_model remains None

            # --- Post-Request Hooks ---
            if self._settings.post_request_hooks:
                logger.debug(
                    f"Executing {len(self._settings.post_request_hooks)} post-request hooks "
                    f"for {request.method} {request.url}"
                )
                for hook in self._settings.post_request_hooks:
                    try:
                        hook(response, parsed_model, 1)  # Always 1 for single request
                    except Exception as e:
                        logger.error(
                            f"Error executing post-request hook {getattr(hook, '__name__', str(hook))}: {e}",
                            exc_info=True,
                        )

            return response, parsed_model

        except httpx.HTTPStatusError as e:
            # This block might be hit if httpx raises before our status check
            if e.response:
                retry_after_from_headers = await self._parse_rate_limit_headers(
                    e.response
                )

            logger.error(
                f"Request failed with status {e.response.status_code}: {e.request.url}"
            )
            if e.response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                if self._settings.enable_rate_limiting:
                    wait_duration = (
                        retry_after_from_headers
                        or self._settings.rate_limit_retry_after_default
                    )
                    logger.info(
                        f"Rate limit hit (429) in HTTPStatusError. Waiting for {wait_duration:.2f}s."
                    )
                    await asyncio.sleep(wait_duration)
                raise RateLimitError(
                    "API rate limit exceeded.", response=e.response, request=e.request
                ) from e
            raise APIError(
                f"API request failed with status {e.response.status_code}",
                response=e.response,
                request=e.request,
            ) from e
        except httpx.TimeoutException as e:
            logger.error(f"Request timed out: {request.url}")
            raise TimeoutError("Request timed out", request=request) from e
        except httpx.NetworkError as e:  # Specific network errors
            logger.error(f"Network error occurred for {request.url}: {e}")
            raise NetworkError(
                f"Network error for {request.url}: {e}", request=request
            ) from e
        except httpx.RequestError as e:  # Other httpx request errors (e.g. connection, read timeouts if not httpx.TimeoutException)
            logger.error(f"HTTP request error for {request.url}: {e}")
            raise BibliofabricRequestError(
                f"HTTP request error for {request.url}: {e}", request=request
            ) from e
        except Exception as e:
            # If response was received before another exception, parse its headers
            if response:
                await self._parse_rate_limit_headers(response)

            logger.exception(
                f"Unexpected error during single request execution to {request.url}: {e}"
            )
            if isinstance(e, BibliofabricError):  # If it's already our error, re-raise
                raise e
            # Keep this as a general fallback
            raise BibliofabricError(
                f"An unexpected error occurred during request execution: {e}",
                request=request,
            ) from e

    def _should_retry_request(self, retry_state: tenacity.RetryCallState) -> bool:
        """Predicate for tenacity: should we retry this request?

        Args:
            retry_state: The current retry state from tenacity.

        Returns:
            bool: True if the request should be retried, False otherwise.
        """
        outcome = retry_state.outcome
        if not outcome:  # Should not happen with reraise=True, but defensive check
            return False

        if outcome.failed:
            exc = outcome.exception()
            url = "N/A"
            request = getattr(exc, "request", None)
            if request:
                url = str(getattr(request, "url", "N/A"))

            # Retry on timeout, network, and rate limit errors
            if isinstance(exc, TimeoutError | NetworkError | RateLimitError):
                logger.warning(f"Retrying due to {type(exc).__name__} for {url}")
                return True
            # Also retry on httpx exceptions
            if isinstance(exc, httpx.TimeoutException | httpx.NetworkError):
                logger.warning(
                    f"Retrying due to {type(exc).__name__} (httpx) for {url}"
                )
                return True

            status_code: int | None = None
            if isinstance(exc, APIError):
                if exc.response is not None:
                    status_code = exc.response.status_code
            elif isinstance(exc, httpx.HTTPStatusError):
                status_code = exc.response.status_code

            if status_code is not None and status_code in self._retryable_status_codes:
                logger.warning(f"Retrying due to status code {status_code} for {url}")
                return True

        return False

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        params: Mapping[str, Any] | None = None,
        json_data: Any | None = None,
        data: Mapping[str, Any] | None = None,
        base_url_override: str | None = None,
        expected_model: type[Any] | None = None,
    ) -> tuple[httpx.Response, Any | None, int]:
        """Make an HTTP request with configured retries for transient errors.

        Args:
            method: HTTP method (GET, POST, etc.).
            path: Request path relative to base URL.
            params: Query parameters.
            json_data: JSON data for request body.
            data: Form data for request body.
            base_url_override: Optional override for the base URL.
            expected_model: Optional Pydantic model for response parsing.

        Returns:
            tuple[httpx.Response, Any | None, int]: The HTTP response, optionally
                parsed model instance, and the number of attempts made.

        Raises:
            Various exceptions depending on failure type after all retries are exhausted.
        """
        # Determine the correct base URL for this request
        _target_base_url = (base_url_override or self._base_url).rstrip("/")
        full_url = f"{_target_base_url}/{path.lstrip('/')}"

        request_data = RequestData(
            method=method,
            url=full_url,
            params=params,
            json_data=json_data,
            data=data,
            # Headers will be populated by auth strategy and pre-request hooks
        )

        # Pre-request rate limit check
        if self._settings.enable_rate_limiting:
            async with self._rate_limit_lock:
                # Check if we have rate limit information
                if (
                    self._rate_limit_remaining is not None
                    and self._rate_limit_limit is not None
                    and self._rate_limit_limit > 0
                ):
                    # Check if remaining requests are below the buffer or zero
                    buffer_threshold = (
                        self._rate_limit_limit
                        * self._settings.rate_limit_buffer_percentage
                    )
                    if (
                        self._rate_limit_remaining <= buffer_threshold
                        or self._rate_limit_remaining == 0
                    ):
                        if self._rate_limit_reset_timestamp is not None:
                            current_time = time.time()
                            wait_time = self._rate_limit_reset_timestamp - current_time
                            if wait_time > 0:
                                logger.info(
                                    f"Rate limit approaching/reached. "
                                    f"Remaining: {self._rate_limit_remaining}/{self._rate_limit_limit}. "
                                    f"Waiting for {wait_time:.2f}s until reset."
                                )
                                await asyncio.sleep(wait_time)
                        elif self._rate_limit_remaining == 0:
                            logger.warning(
                                f"Rate limit reset time {self._rate_limit_reset_timestamp} is past "
                                f"but remaining requests is {self._rate_limit_remaining}. "
                                f"Waiting for default: {self._settings.rate_limit_retry_after_default}s."
                            )
                            await asyncio.sleep(
                                self._settings.rate_limit_retry_after_default
                            )
                elif self._rate_limit_remaining == 0 and self._rate_limit_limit is None:
                    # If remaining is 0 (e.g. from a 429) but we never got a limit header
                    logger.warning(
                        f"Rate limit remaining is 0 (likely from a 429) but no limit/reset headers were ever parsed. "
                        f"Waiting for default: {self._settings.rate_limit_retry_after_default}s as a precaution."
                    )
                    await asyncio.sleep(self._settings.rate_limit_retry_after_default)

        # Apply authentication *before* retry loop setup, fail fast on auth issues
        try:
            # Build a temporary request to apply auth and get initial headers
            temp_request_for_auth = request_data.build_request()
            await self._auth_strategy.async_authenticate(temp_request_for_auth)
            # Update request_data.headers with those from the auth strategy
            request_data.headers = dict(temp_request_for_auth.headers)
        except AuthError as e:
            logger.error(f"Authentication failed before request: {e}")
            raise e
        except Exception as e:
            logger.exception(f"Unexpected error during pre-request authentication: {e}")
            raise BibliofabricError(f"Unexpected authentication error: {e}") from e

        # Prepare retry strategy
        retry_strategy = AsyncRetrying(
            stop=stop_after_attempt(
                self._settings.max_retries + 1
            ),  # +1 for initial attempt
            wait=wait_exponential(
                multiplier=self._settings.backoff_factor,
            ),
            retry=self._should_retry_request,
            reraise=True,  # Reraise the exception if all retries fail
            before_sleep=self._before_retry_sleep,  # Log before sleeping
        )

        try:
            response, parsed_model = await retry_strategy(
                self._execute_single_request, request_data, expected_model
            )
            return response, parsed_model, retry_strategy.statistics["attempt_number"]
        except Exception as e:
            logger.error(f"Request failed after multiple retries: {e}")
            raise

    async def _before_retry_sleep(self, retry_state: tenacity.RetryCallState) -> None:
        """Log details before tenacity sleeps between retries.

        Args:
            retry_state: The current retry state from tenacity.
        """
        if not retry_state.outcome:  # Should not happen
            return

        exc = retry_state.outcome.exception()
        url = "N/A"
        request_info = ""
        if exc and hasattr(exc, "request") and getattr(exc, "request", None):
            request = getattr(exc, "request", None)
            if request:
                url = str(getattr(request, "url", "N/A"))
                method = str(getattr(request, "method", "N/A"))
                request_info = f"for {method} {url}"

        sleep_time = (
            getattr(retry_state.next_action, "sleep", 0)
            if retry_state.next_action
            else 0
        )
        logger.info(
            f"Retrying request {request_info} in {sleep_time:.2f} seconds "
            f"after {retry_state.attempt_number} attempt(s) due to: {type(exc).__name__} - {exc}"
        )

    def _generate_cache_key(
        self, method: str, url: str, params: Mapping[str, Any] | None = None
    ) -> str:
        """Generate a cache key from the request method, URL, and parameters.

        Args:
            method: HTTP method (e.g., 'GET', 'POST').
            url: Full URL for the request.
            params: Query parameters dict.

        Returns:
            str: A unique cache key string.
        """

        # Start with method and URL
        key_parts = [method.upper(), url]

        # Add sorted parameters if they exist
        if params:
            # Sort parameters to ensure consistent cache keys
            sorted_params = json.dumps(params, sort_keys=True, separators=(",", ":"))
            key_parts.append(sorted_params)

        # Create a hash of the combined key parts
        cache_key_string = "|".join(key_parts)
        return hashlib.md5(cache_key_string.encode("utf-8")).hexdigest()

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,  # Alias for json_data
        json_data: Any | None = None,
        data: Mapping[str, Any] | None = None,
        expected_model: type[Any] | None = None,
        base_url_override: str | None = None,
    ) -> httpx.Response | Any:
        """Perform an asynchronous HTTP request to the specified API path.

        This method provides the main interface for making API requests with automatic
        retries, caching (for GET requests), rate limiting, and error handling.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.).
            path: Request path relative to the base URL.
            params: Query parameters as a mapping.
            json: JSON data for request body (alias for json_data).
            json_data: JSON data for request body.
            data: Form data for request body.
            expected_model: Optional Pydantic model class for response validation.
            base_url_override: Optional override for the base URL.

        Returns:
            httpx.Response | Any: Raw httpx.Response if no expected_model provided,
                otherwise the parsed Pydantic model instance, falling back to
                raw response if parsing fails.

        Note:
            GET requests are automatically cached when caching is enabled and
            an expected_model is provided. Cache hits return the parsed model
            directly without making an HTTP request.
        """
        actual_json_data = json_data if json_data is not None else json
        if json is not None and json_data is not None:
            logger.warning(
                "Both 'json' and 'json_data' provided to request; using 'json_data'."
            )

        cache_key: str | None = None

        # --- Cache Check (for GET requests) ---
        if self._cache is not None and method.upper() == "GET":
            _target_base_url = (base_url_override or self._base_url).rstrip("/")
            full_url = f"{_target_base_url}/{path.lstrip('/')}"
            cache_key = self._generate_cache_key(method, full_url, params)

            cached_item = self._cache.get(cache_key)
            if cached_item is not None:
                # Assuming the cached item is the already parsed Pydantic model
                logger.debug(f"Cache hit for key: {cache_key}")
                if expected_model and not isinstance(cached_item, expected_model):
                    logger.warning(
                        f"Cache hit for {cache_key}, but type mismatch. "
                        f"Expected {expected_model}, got {type(cached_item)}. Discarding cache."
                    )
                    self._cache.pop(cache_key, None)  # Treat as cache miss
                else:
                    logger.debug(f"Returning cached parsed model for key: {cache_key}")
                    return cached_item  # cached_item is the parsed_model

        # --- Execute Request (if not a cache hit or not cacheable) ---
        response, parsed_model, attempts = await self._request_with_retry(
            method=method,
            path=path,
            params=params,
            json_data=actual_json_data,
            data=data,
            base_url_override=base_url_override,
            expected_model=expected_model,
        )

        # --- Cache Store (for successful GET requests with a successfully parsed model) ---
        if (
            self._cache is not None
            and cache_key is not None  # Implies GET and cache enabled
            and method.upper() == "GET"
            and HTTPStatus.OK
            <= response.status_code
            < HTTPStatus.MULTIPLE_CHOICES  # 2xx
        ):
            if expected_model and parsed_model is not None:
                # Ensure what we are caching is indeed of the expected_model type
                if isinstance(parsed_model, expected_model):
                    self._cache[cache_key] = (
                        parsed_model  # Store the already parsed model
                    )
                    logger.debug(f"Cached parsed model for key: {cache_key}")
                else:
                    logger.warning(
                        f"Attempted to cache for key {cache_key}, but parsed_model type "
                        f"{type(parsed_model)} does not match expected_model {expected_model}. Not caching."
                    )
            elif expected_model and parsed_model is None:
                logger.debug(
                    f"GET request for {cache_key} successful, but model parsing failed or no model to parse. Not caching."
                )

        # --- Standard Response Handling ---
        if expected_model:
            if parsed_model is not None and isinstance(parsed_model, expected_model):
                return parsed_model  # Return the successfully parsed model
            # Parsing failed inside _execute_single_request (parsed_model is None)
            # or it's not of the expected type (should be rare if parsing succeeded).
            logger.warning(
                f"Expected model {expected_model.__name__} but parsing failed, model was None, "
                f"or type mismatch for {method} {path}. Returning raw response."
            )
            return response  # Fallback to raw response

        return response  # Default: return raw response if no expected_model

    async def aclose(self) -> None:
        """Close the underlying HTTP client and any auth-specific clients.

        This method should be called when the client is no longer needed to
        properly clean up resources like HTTP connections and authentication
        clients.
        """
        logger.info(
            f"BaseApiClient.aclose() called. Client ID: {id(self)}. HTTP client to close: {self._should_close_client and self._http_client is not None}. HTTP client closed: {self._http_client.is_closed if self._http_client else 'N/A'}"
        )
        if (
            self._should_close_client
            and self._http_client
            and not self._http_client.is_closed
        ):
            await self._http_client.aclose()
            logger.info(
                f"BaseApiClient internal HTTP client closed. Client ID: {id(self)}."
            )
        elif self._http_client and self._http_client.is_closed:
            logger.info(
                f"BaseApiClient.aclose(): HTTP client was already closed. Client ID: {id(self)}"
            )
        # Close auth strategy client if it has an async_close method
        if hasattr(self._auth_strategy, "async_close") and callable(
            self._auth_strategy.async_close
        ):
            await self._auth_strategy.async_close()  # type: ignore

    async def __aenter__(self) -> Self:
        """Enter the async context manager.

        Returns:
            Self: The client instance for use in async context.
        """
        logger.info(
            f"BaseApiClient.__aenter__() called. Client ID: {id(self)}. HTTP client closed: {self._http_client.is_closed if self._http_client else 'N/A'}"
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """Exit the async context manager and clean up resources.

        Args:
            exc_type: Exception type if an exception occurred.
            exc_val: Exception value if an exception occurred.
            exc_tb: Exception traceback if an exception occurred.
        """
        logger.info(
            f"BaseApiClient.__aexit__() called. Client ID: {id(self)}. HTTP client closed before aclose: {self._http_client.is_closed if self._http_client else 'N/A'}"
        )
        await self.aclose()
        logger.info(
            f"BaseApiClient.__aexit__() finished. Client ID: {id(self)}. HTTP client closed after aclose: {self._http_client.is_closed if self._http_client else 'N/A'}"
        )
