"""Exception hierarchy for bibliofabric-family clients.

Every exception carries the ``httpx.Request``/``httpx.Response`` of the failed
call when they are available, and redacts credential query parameters from URLs
in its string form.
"""

from typing import Any

import httpx

from .utils import sanitize_url


class BibliofabricError(Exception):
    """Base class for all bibliofabric errors."""

    def __init__(
        self,
        message: str,
        *,
        request: httpx.Request | None = None,
        response: httpx.Response | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.request = request
        self.response = response

    def __str__(self) -> str:
        message = sanitize_url(self.message)
        if self.response is not None:
            url = getattr(self.response, "request", None)
            suffix = (
                f" (status: {self.response.status_code}, URL: {sanitize_url(url.url)})"
                if url is not None
                else ""
            )
            return f"{message}{suffix}"
        if self.request is not None:
            return f"{message} (URL: {sanitize_url(self.request.url)})"
        return message


class ConfigurationError(BibliofabricError):
    """The library was misconfigured (missing credentials, disabled feature)."""


class AuthError(BibliofabricError):
    """Authentication failed, e.g. fetching an OAuth token."""


class NetworkError(BibliofabricError):
    """A network failure occurred (DNS, connection refused, reset)."""


class TimeoutError(BibliofabricError, TimeoutError):
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
    ) -> None:
        super().__init__(message, request=request, response=response)
        self.body = body


class NotFoundError(APIError):
    """The API answered 404 Not Found."""


class RateLimitError(APIError):
    """The API answered 429 Too Many Requests."""


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
    ) -> None:
        super().__init__(message, request=request, response=response)
        self.raw = raw
        self.error = error
        self.model_name = model_name
