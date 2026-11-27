"""Exception hierarchy for bibliofabric-family clients.

Every exception carries the ``httpx.Request``/``httpx.Response`` of the failed
call when they are available, and redacts credential query parameters from URLs
in its string form.
"""

import builtins
import json
from collections.abc import Collection
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError as PydanticValidationError

from .utils import sanitize_url

_ERROR_BODY_KEYS = (
    "reason",
    "error",
    "message",
    "detail",
    "error_description",
    "title",
)
_MAX_BODY_SUMMARY_CHARS = 250


def _extract_request(response: httpx.Response | None) -> httpx.Request | None:
    """Return ``response.request`` when attached, else ``None``."""
    if response is None:
        return None
    try:
        return response.request
    except RuntimeError:
        return None


def _truncate(text: str, max_length: int = _MAX_BODY_SUMMARY_CHARS) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_length:
        return compact
    return f"{compact[: max_length - 3].rstrip()}..."


def _summarize_body(
    body: Any,
    response: httpx.Response | None = None,
    *,
    extra_params: Collection[str] = (),
) -> str | None:
    """Build a concise, sanitized summary of an upstream error body."""
    if isinstance(body, dict):
        parts: list[str] = []
        for key in _ERROR_BODY_KEYS:
            value = body.get(key)
            if value is None or value == "":
                continue
            if isinstance(value, str | int | float | bool):
                parts.append(f"{key}={value}")
            else:
                try:
                    encoded = json.dumps(
                        value, ensure_ascii=False, separators=(",", ":")
                    )
                except (TypeError, ValueError):
                    encoded = str(value)
                parts.append(f"{key}={encoded}")
        if parts:
            return _truncate(sanitize_url(", ".join(parts), extra_params=extra_params))
        if body:
            try:
                encoded = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
            except (TypeError, ValueError):
                encoded = str(body)
            return _truncate(sanitize_url(encoded, extra_params=extra_params))
        return None
    if isinstance(body, str):
        stripped = body.strip()
        return (
            _truncate(sanitize_url(stripped, extra_params=extra_params))
            if stripped
            else None
        )
    if body is not None:
        try:
            encoded = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
        except (TypeError, ValueError):
            encoded = str(body)
        return (
            _truncate(sanitize_url(encoded, extra_params=extra_params))
            if encoded
            else None
        )
    if response is not None:
        try:
            text = response.text.strip()
        except (httpx.ResponseNotRead, UnicodeDecodeError):
            return None
        if text:
            return _truncate(sanitize_url(text, extra_params=extra_params))
    return None


class BibliofabricError(Exception):
    """Base class for all bibliofabric errors."""

    def __init__(
        self,
        message: str,
        *,
        request: httpx.Request | None = None,
        response: httpx.Response | None = None,
        redacted_query_params: Collection[str] = (),
    ) -> None:
        super().__init__(message)
        self.message = message
        self.response = response
        self.request = request if request is not None else _extract_request(response)
        self._redacted_query_params: frozenset[str] = frozenset(redacted_query_params)

    @property
    def status_code(self) -> int | None:
        """HTTP status code of the response, when available."""
        return self.response.status_code if self.response is not None else None

    def __str__(self) -> str:
        extra = self._redacted_query_params
        message = sanitize_url(self.message, extra_params=extra)
        request = _extract_request(self.response) or self.request
        if self.response is not None:
            if request is not None:
                return (
                    f"{message} (status: {self.response.status_code}, "
                    f"URL: {sanitize_url(request.url, extra_params=extra)})"
                )
            return f"{message} (status: {self.response.status_code})"
        if request is not None:
            return f"{message} (URL: {sanitize_url(request.url, extra_params=extra)})"
        return message


class ConfigurationError(BibliofabricError):
    """The library was misconfigured (missing credentials, disabled feature)."""


class AuthError(BibliofabricError):
    """Authentication failed, e.g. 401/403 or fetching an OAuth token."""

    def __init__(
        self,
        message: str,
        *,
        body: Any = None,
        request: httpx.Request | None = None,
        response: httpx.Response | None = None,
        redacted_query_params: Collection[str] = (),
    ) -> None:
        super().__init__(
            message,
            request=request,
            response=response,
            redacted_query_params=redacted_query_params,
        )
        self.body = body

    def __str__(self) -> str:
        base = super().__str__()
        summary = _summarize_body(
            self.body, self.response, extra_params=self._redacted_query_params
        )
        return f"{base}: {summary}" if summary else base


class NetworkError(BibliofabricError):
    """A network failure occurred (DNS, connection refused, reset)."""


class TimeoutError(BibliofabricError, builtins.TimeoutError):
    """The request exceeded its timeout; also a builtin ``TimeoutError``."""


class APIError(BibliofabricError):
    """The API answered with an error status that has no dedicated subclass.

    ``body`` holds the parsed JSON error payload when the response body was
    JSON (for example OpenAlex's ``{"reason": "daily_budget"}``), else ``None``.
    """

    def __init__(
        self,
        message: str,
        *,
        body: Any = None,
        request: httpx.Request | None = None,
        response: httpx.Response | None = None,
        redacted_query_params: Collection[str] = (),
    ) -> None:
        super().__init__(
            message,
            request=request,
            response=response,
            redacted_query_params=redacted_query_params,
        )
        self.body = body

    def __str__(self) -> str:
        base = super().__str__()
        summary = _summarize_body(
            self.body, self.response, extra_params=self._redacted_query_params
        )
        return f"{base}: {summary}" if summary else base


class NotFoundError(APIError):
    """The API answered 404 Not Found."""


class RateLimitError(APIError):
    """The API answered 429 Too Many Requests."""

    def __init__(
        self,
        message: str,
        *,
        body: Any = None,
        retry_after: float | None = None,
        request: httpx.Request | None = None,
        response: httpx.Response | None = None,
        redacted_query_params: Collection[str] = (),
    ) -> None:
        super().__init__(
            message,
            body=body,
            request=request,
            response=response,
            redacted_query_params=redacted_query_params,
        )
        self.retry_after = retry_after


class ValidationError(BibliofabricError):
    """A response record failed pydantic validation.

    Carries the raw payload (``raw``), the pydantic error (``error``) and the
    name of the model that rejected the payload (``model_name``).
    """

    def __init__(
        self,
        message: str,
        *,
        raw: object,
        error: Exception,
        model_name: str | None = None,
        request: httpx.Request | None = None,
        response: httpx.Response | None = None,
        redacted_query_params: Collection[str] = (),
    ) -> None:
        super().__init__(
            message,
            request=request,
            response=response,
            redacted_query_params=redacted_query_params,
        )
        self.raw = raw
        self.error = error
        self.model_name = model_name


def validate_model[M: BaseModel](
    model: type[M],
    data: Any,
    *,
    request: httpx.Request | None = None,
    response: httpx.Response | None = None,
) -> M:
    """Validate ``data`` against ``model``, wrapping failures in :class:`ValidationError`."""
    try:
        return model.model_validate(data)
    except PydanticValidationError as error:
        raise ValidationError(
            f"Failed to validate {model.__name__}: {error}",
            raw=data,
            error=error,
            model_name=model.__name__,
            request=request,
            response=response,
        ) from error


__all__ = [
    "APIError",
    "AuthError",
    "BibliofabricError",
    "ConfigurationError",
    "NetworkError",
    "NotFoundError",
    "RateLimitError",
    "TimeoutError",
    "ValidationError",
    "validate_model",
]
