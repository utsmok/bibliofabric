"""Generic API client for bibliofabric-family libraries.

``BaseApiClient`` owns the HTTP lifecycle: default headers, redirects,
retries honoring ``Retry-After``, per-request-class pacing, auth strategy
application, status-to-exception mapping, streaming responses, and credential
redaction in debug logs. It never parses models.
"""

import logging
import math
from collections.abc import AsyncGenerator, Collection, Mapping
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from http import HTTPStatus
from typing import Any, Self

import httpx
import tenacity
from tenacity import AsyncRetrying, stop_after_attempt, wait_random_exponential

from ..auth import AuthStrategy, NoAuth
from ..config import BaseApiSettings
from ..exceptions import (
    APIError,
    AuthError,
    BibliofabricError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    TimeoutError,
)
from ..unwrap import ResponseUnwrapper
from ..utils import sanitize_headers, sanitize_url
from ._concurrency import Limiter

logger = logging.getLogger(__name__)

RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})
IDEMPOTENT_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "PUT", "DELETE"})


def _retry_after_seconds(response: httpx.Response) -> float | None:
    """Return the Retry-After delay in seconds, or ``None`` when absent or unparseable."""
    header = response.headers.get("Retry-After")
    if header is None:
        return None
    header = header.strip()
    try:
        seconds = float(header)
    except ValueError:
        pass
    else:
        return max(0.0, seconds) if math.isfinite(seconds) else None
    try:
        when = parsedate_to_datetime(header)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    return max(0.0, (when - datetime.now(UTC)).total_seconds())


def _error_body(response: httpx.Response) -> Any:
    """Return the parsed JSON body of an error response, or ``None``."""
    try:
        return response.json()
    except Exception:
        return None


def _error_for_status(
    response: httpx.Response,
    *,
    redacted_query_params: Collection[str] = (),
) -> BibliofabricError:
    """Map an error status to the bibliofabric exception hierarchy."""
    status = response.status_code
    message = f"API request failed with status {status}"
    body = _error_body(response)
    if status == HTTPStatus.NOT_FOUND:
        return NotFoundError(
            message,
            body=body,
            response=response,
            redacted_query_params=redacted_query_params,
        )
    if status == HTTPStatus.TOO_MANY_REQUESTS:
        return RateLimitError(
            message,
            body=body,
            retry_after=_retry_after_seconds(response),
            response=response,
            redacted_query_params=redacted_query_params,
        )
    if status in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
        return AuthError(
            message,
            body=body,
            response=response,
            redacted_query_params=redacted_query_params,
        )
    return APIError(
        message,
        body=body,
        response=response,
        redacted_query_params=redacted_query_params,
    )


class _RetryAfterWait(tenacity.wait.wait_base):
    """Retry-After when the server sent one, else jittered exponential backoff.

    Both are capped at ``max_retry_wait``.
    """

    def __init__(self, max_retry_wait: float) -> None:
        self._backoff = wait_random_exponential(multiplier=1, max=max_retry_wait)
        self._max_retry_wait = max_retry_wait

    def __call__(self, retry_state: tenacity.RetryCallState) -> float:
        outcome = retry_state.outcome
        exception = outcome.exception() if outcome is not None else None
        response = getattr(exception, "response", None)
        if isinstance(response, httpx.Response):
            delay = _retry_after_seconds(response)
            if delay is not None:
                return min(delay, self._max_retry_wait)
        return self._backoff(retry_state)


class BaseApiClient:
    """Generic HTTP client; subclass per API with base_url and unwrapper."""

    def __init__(
        self,
        *,
        base_url: str,
        settings: BaseApiSettings,
        unwrapper: ResponseUnwrapper,
        auth: AuthStrategy | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._settings = settings
        self._auth: AuthStrategy = auth if auth is not None else NoAuth()
        self._unwrapper = unwrapper
        rate_limits: dict[str, float | None] = {
            "default": settings.max_requests_per_second
        }
        rate_limits.update(settings.rate_limits)
        self._limiter = Limiter(rate_limits, settings.max_concurrency)
        self._should_close_client = http_client is None
        self._http_client = (
            http_client if http_client is not None else self._create_http_client()
        )

    @property
    def base_url(self) -> str:
        """The normalized base URL this client sends requests to."""
        return self._base_url

    @property
    def unwrapper(self) -> ResponseUnwrapper:
        """The response unwrapper this client was built with."""
        return self._unwrapper

    @property
    def settings(self) -> BaseApiSettings:
        """The settings this client was built with."""
        return self._settings

    @property
    def default_headers(self) -> Mapping[str, str]:
        """Headers sent with every request; per-call ``headers`` entries win.

        Override to pin one representation for a whole API, for example
        ``{"Accept": "application/vnd.orcid+json"}`` for ORCID, whose default
        is XML.
        """
        return {}

    @property
    def _redacted_query_params(self) -> frozenset[str]:
        return frozenset(getattr(self._auth, "redacted_query_params", ()))

    @property
    def _redacted_headers(self) -> frozenset[str]:
        return frozenset(getattr(self._auth, "redacted_headers", ()))

    def _sanitize_url(self, value: object) -> str:
        return sanitize_url(value, extra_params=self._redacted_query_params)

    def _sanitize_headers(self, headers: Mapping[str, str]) -> dict[str, str]:
        return sanitize_headers(headers, extra_headers=self._redacted_headers)

    def _invalidate_auth_token(self) -> bool:
        invalidate = getattr(self._auth, "invalidate_token", None)
        if callable(invalidate):
            invalidate()
            return True
        return False

    def _create_http_client(self) -> httpx.AsyncClient:
        timeout: float | httpx.Timeout = (
            httpx.Timeout(
                self._settings.timeout,
                connect=self._settings.connect_timeout,
            )
            if self._settings.connect_timeout is not None
            else self._settings.timeout
        )
        limits = httpx.Limits(
            max_connections=max(20, self._settings.max_concurrency * 2),
            max_keepalive_connections=max(10, self._settings.max_concurrency),
        )
        return httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout,
            limits=limits,
            follow_redirects=self._settings.follow_redirects,
            headers={"User-Agent": self._settings.effective_user_agent()},
        )

    def rate_class(self, request: httpx.Request) -> str:
        """Return the request's rate class for the limiter.

        The default puts every request in the ``"default"`` class, paced at
        ``max_requests_per_second``. Override to route requests into the
        classes declared in ``BaseApiSettings.rate_limits``.
        """
        return "default"

    def on_response(self, response: httpx.Response) -> None:
        """Hook invoked after every HTTP response, before status errors raise.

        Override to inspect rate-limit headers, response timings, or telemetry.
        """

    def is_retryable(self, response: httpx.Response) -> bool:
        """Whether a response should be retried.

        Override to veto retries for statuses the default treats as transient,
        for example OpenAlex 429s with ``reason: "daily_budget"``.
        """
        return response.status_code in RETRYABLE_STATUS_CODES

    def _should_retry(
        self,
        retry_state: tenacity.RetryCallState,
        *,
        retry: bool | None = None,
    ) -> bool:
        if retry is False:
            return False
        outcome = retry_state.outcome
        if outcome is None or not outcome.failed:
            return False
        exception = outcome.exception()
        if retry is None:
            request = getattr(exception, "request", None)
            if request is None and retry_state.args:
                candidate = retry_state.args[0]
                if isinstance(candidate, httpx.Request):
                    request = candidate
            if (
                isinstance(request, httpx.Request)
                and request.method.upper() not in IDEMPOTENT_METHODS
            ):
                return False
        if isinstance(exception, TimeoutError | NetworkError):
            return True
        if isinstance(exception, APIError):
            response = exception.response
            return response is not None and self.is_retryable(response)
        return False

    def parse_json(self, response: httpx.Response) -> Any:
        """Decode a JSON response body, raising :class:`APIError` on invalid JSON."""
        try:
            return response.json()
        except ValueError as error:
            raise APIError(
                f"API returned invalid JSON (status {response.status_code}): {error}",
                response=response,
                redacted_query_params=self._redacted_query_params,
            ) from error

    def _clone_request(self, request: httpx.Request) -> httpx.Request:
        """Create a fresh ``httpx.Request`` copy so retries never mutate prior attempts."""
        return httpx.Request(
            request.method,
            request.url,
            headers=request.headers.copy(),
            content=request.content,
            extensions=dict(request.extensions),
        )

    async def _send_once(
        self, template: httpx.Request, *, follow_redirects: bool | None = None
    ) -> httpx.Response:
        """Authenticate, throttle, send once, refresh token once on 401, and map errors.

        ``follow_redirects`` overrides the client's redirect setting for this
        send; ``None`` keeps the client default.
        """
        follow = (
            httpx.USE_CLIENT_DEFAULT if follow_redirects is None else follow_redirects
        )
        for attempt in range(2):
            request = self._clone_request(template)
            await self._auth.async_authenticate(request)
            logger.debug(
                "Sending request: %s %s",
                request.method,
                self._sanitize_url(request.url),
            )
            logger.debug("Request headers: %s", self._sanitize_headers(request.headers))
            await self._limiter.acquire(self.rate_class(request))
            try:
                response = await self._http_client.send(
                    request, follow_redirects=follow
                )
            except httpx.TimeoutException as error:
                raise TimeoutError(
                    f"Request timed out: {self._sanitize_url(request.url)}",
                    request=request,
                    redacted_query_params=self._redacted_query_params,
                ) from error
            except httpx.RequestError as error:
                raise NetworkError(
                    f"Request failed for {self._sanitize_url(request.url)}: "
                    f"{self._sanitize_url(error)}",
                    request=request,
                    redacted_query_params=self._redacted_query_params,
                ) from error
            finally:
                self._limiter.release()
            logger.debug(
                "Received response: %s for %s",
                response.status_code,
                self._sanitize_url(request.url),
            )
            self.on_response(response)
            if (
                response.status_code == HTTPStatus.UNAUTHORIZED
                and attempt == 0
                and self._invalidate_auth_token()
            ):
                logger.debug(
                    "Received 401 for %s; invalidating cached token and retrying once",
                    self._sanitize_url(request.url),
                )
                continue
            if response.status_code >= HTTPStatus.BAD_REQUEST:
                raise _error_for_status(
                    response,
                    redacted_query_params=self._redacted_query_params,
                )
            return response
        raise RuntimeError(
            "Unreachable: token refresh loop exhausted"
        )  # pragma: no cover

    def _resolve_url(self, path: str) -> str:
        """Resolve relative ``path`` against ``self._base_url`` when needed."""
        if path.startswith(("http://", "https://")):
            return path
        if not str(self._http_client.base_url):
            return f"{self._base_url}/{path.lstrip('/')}"
        return path

    def _effective_headers(
        self, headers: Mapping[str, str] | None
    ) -> dict[str, str] | None:
        """Return ``headers`` with the caller-owned client UA rule and ``default_headers`` applied."""
        request_headers = dict(headers) if headers is not None else None
        if not self._should_close_client:
            has_explicit_ua = request_headers is not None and any(
                key.lower() == "user-agent" for key in request_headers
            )
            client_ua = self._http_client.headers.get("user-agent", "")
            if not has_explicit_ua and (
                not client_ua or client_ua.startswith("python-httpx/")
            ):
                request_headers = {
                    "User-Agent": self._settings.effective_user_agent(),
                    **(request_headers or {}),
                }
        defaults = self.default_headers
        if defaults:
            overrides = {key.lower() for key in request_headers or {}}
            request_headers = {
                **{
                    key: value
                    for key, value in defaults.items()
                    if key.lower() not in overrides
                },
                **(request_headers or {}),
            }
        return request_headers

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        data: Mapping[str, Any] | None = None,
        content: str | bytes | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float | httpx.Timeout | None = None,
        retry: bool | None = None,
        follow_redirects: bool | None = None,
    ) -> httpx.Response:
        """Send a request with retries and return the response.

        By default (``retry=None``), automatic retries apply only to idempotent
        HTTP methods (``GET``, ``HEAD``, ``OPTIONS``, ``PUT``, ``DELETE``). Pass
        ``retry=True`` to allow retries on non-idempotent methods (such as
        read-only ``POST`` batch APIs), or ``retry=False`` to disable retries
        for this call.

        ``follow_redirects=None`` leaves the decision to
        ``settings.follow_redirects``. Pass ``False`` to receive the 3xx
        response itself (for example to read its ``Location`` header), or
        ``True`` to follow a resolver that redirects to another host.

        Raises on status >= 400: 404 is :class:`NotFoundError`, 429 is
        :class:`RateLimitError`, 401/403 is :class:`AuthError`, other statuses
        are :class:`APIError`. Network failures raise :class:`NetworkError`,
        timeouts :class:`TimeoutError`.
        """
        request = self._http_client.build_request(
            method,
            self._resolve_url(path),
            params=params,
            json=json,
            data=data,
            content=content,
            headers=self._effective_headers(headers),
            timeout=httpx.USE_CLIENT_DEFAULT if timeout is None else timeout,
        )
        if retry is False:
            return await self._send_once(request, follow_redirects=follow_redirects)
        retrying = AsyncRetrying(
            stop=stop_after_attempt(self._settings.max_retries + 1),
            wait=_RetryAfterWait(max_retry_wait=self._settings.max_retry_wait),
            retry=lambda state: self._should_retry(state, retry=retry),
            reraise=True,
        )
        return await retrying(
            self._send_once, request, follow_redirects=follow_redirects
        )

    @asynccontextmanager
    async def stream(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float | httpx.Timeout | None = None,
        follow_redirects: bool | None = None,
    ) -> AsyncGenerator[httpx.Response]:
        """Open a streaming HTTP response with auth, rate limiting, and error mapping.

        Yields the open :class:`httpx.Response` for incremental consumption (for
        example downloading Zenodo files or large dumps). Calls
        :meth:`on_response` before raising typed errors on status >= 400, and
        refreshes cached OAuth tokens once on HTTP 401. ``follow_redirects``
        overrides ``settings.follow_redirects`` for this call, as in
        :meth:`request`.
        """
        effective_timeout = httpx.USE_CLIENT_DEFAULT if timeout is None else timeout
        follow = (
            httpx.USE_CLIENT_DEFAULT if follow_redirects is None else follow_redirects
        )
        for attempt in range(2):
            request = self._http_client.build_request(
                method,
                self._resolve_url(path),
                params=params,
                headers=self._effective_headers(headers),
                timeout=effective_timeout,
            )
            await self._auth.async_authenticate(request)
            logger.debug(
                "Sending request: %s %s",
                request.method,
                self._sanitize_url(request.url),
            )
            logger.debug("Request headers: %s", self._sanitize_headers(request.headers))
            should_retry_auth = False
            await self._limiter.acquire(self.rate_class(request))
            try:
                try:
                    async with self._http_client.stream(
                        request.method,
                        request.url,
                        headers=request.headers,
                        timeout=effective_timeout,
                        follow_redirects=follow,
                    ) as response:
                        logger.debug(
                            "Received response: %s for %s",
                            response.status_code,
                            self._sanitize_url(request.url),
                        )
                        self.on_response(response)
                        if (
                            response.status_code == HTTPStatus.UNAUTHORIZED
                            and attempt == 0
                            and self._invalidate_auth_token()
                        ):
                            logger.debug(
                                "Received 401 for %s; invalidating cached token and retrying once",
                                self._sanitize_url(request.url),
                            )
                            should_retry_auth = True
                        elif response.status_code >= HTTPStatus.BAD_REQUEST:
                            await response.aread()
                            raise _error_for_status(
                                response,
                                redacted_query_params=self._redacted_query_params,
                            )
                        else:
                            yield response
                            return
                except httpx.TimeoutException as error:
                    raise TimeoutError(
                        f"Request timed out: {self._sanitize_url(request.url)}",
                        request=request,
                        redacted_query_params=self._redacted_query_params,
                    ) from error
                except httpx.RequestError as error:
                    raise NetworkError(
                        f"Request failed for {self._sanitize_url(request.url)}: "
                        f"{self._sanitize_url(error)}",
                        request=request,
                        redacted_query_params=self._redacted_query_params,
                    ) from error
            finally:
                self._limiter.release()
            if not should_retry_auth:
                return

    async def get_json(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        """Send a GET and return the parsed JSON body."""
        response = await self.request("GET", path, params=params, headers=headers)
        return self.parse_json(response)

    async def aclose(self) -> None:
        """Close the HTTP client when owned, and the auth strategy's resources."""
        try:
            if self._should_close_client and not self._http_client.is_closed:
                await self._http_client.aclose()
        finally:
            await self._auth.async_close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        await self.aclose()
