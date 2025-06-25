"""Custom exception classes for the Bibliofabric library."""

import httpx


class BibliofabricError(Exception):
    """Base exception class for all Bibliofabric errors."""

    def __init__(
        self,
        message: str,
        *,
        response: httpx.Response | None = None,
        request: httpx.Request | None = None,
    ):
        """Initializes the base exception.

        Args:
            message: The error message.
            response: Optional httpx.Response object associated with the error.
            request: Optional httpx.Request object associated with the error.
        """
        super().__init__(message)
        self.message = message
        self.response = response
        self.request = request

    def __str__(self) -> str:
        if self.response:
            # Prefer response info if available
            url_info = getattr(getattr(self.response, "request", None), "url", "N/A")
            return (
                f"{self.message} (Status: {self.response.status_code}, URL: {url_info})"
            )
        # Check type before accessing attribute
        if isinstance(self.request, httpx.Request):
            # Fallback to request info if response is missing and request is valid
            return f"{self.message} (URL: {self.request.url})"
        # Default message if neither response nor valid request is available
        return self.message


class APIError(BibliofabricError):
    """Represents a generic error returned by an API (non-specific 4xx/5xx)."""

    # No additional methods needed currently


class NotFoundError(APIError):
    """Represents a resource not found error (404 Not Found)."""

    # No additional methods needed currently


class ValidationError(BibliofabricError):
    """Represents a request validation error (e.g., invalid parameters, 400 Bad Request).

    Can also be raised for client-side validation issues before sending request.
    """

    # No additional methods needed currently


class RateLimitError(APIError):
    """Represents hitting the API rate limit (429 Too Many Requests)."""

    # No additional methods needed currently


class TimeoutError(BibliofabricError):
    """Represents a request timeout error."""

    def __init__(self, message: str, *, request: httpx.Request | None = None):
        # Timeout errors typically don't have a response, but do have the request
        super().__init__(message, response=None)  # Base class handles message
        self.request = request  # Store the request associated with the timeout

    def __str__(self) -> str:
        if self.request:
            return f"{self.message} (URL: {self.request.url})"
        return self.message


class NetworkError(BibliofabricError):
    """Represents a network connection error (e.g., DNS, connection refused)."""

    def __init__(self, message: str, *, request: httpx.Request | None = None):
        # Network errors might not have a response, but have the failing request
        super().__init__(message, response=None)
        self.request = request

    def __str__(self) -> str:
        if self.request:
            return f"{self.message} (URL: {self.request.url})"
        return self.message


class ConfigurationError(BibliofabricError):
    """Represents an error in the library's configuration."""

    def __init__(self, message: str):
        # Configuration errors typically don't have an HTTP response
        super().__init__(message, response=None)


class AuthError(BibliofabricError):
    """Raised when an authentication error occurs, e.g., fetching a token fails."""
