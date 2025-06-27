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
    """Represents a request timeout error.

    This error is raised when an HTTP request does not complete within the configured timeout.
    """

    def __init__(self, message: str, *, request: httpx.Request | None = None):
        """Initializes the TimeoutError.

        Args:
            message: The error message.
            request: The httpx.Request object associated with the timeout.
        """
        super().__init__(message, request=request, response=None)

    def __str__(self) -> str:
        if self.request:
            return f"{self.message} (URL: {self.request.url})"
        return self.message


class NetworkError(BibliofabricError):
    """Represents a network connection error (e.g., DNS resolution failure, connection refused).

    This error indicates a problem in establishing or maintaining a network connection
    to the server during an HTTP request.
    """

    def __init__(self, message: str, *, request: httpx.Request | None = None):
        """Initializes the NetworkError.

        Args:
            message: The error message.
            request: The httpx.Request object associated with the network error.
        """
        super().__init__(message, request=request, response=None)

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


class BibliofabricRequestError(BibliofabricError):
    """Represents an error during the HTTP request process itself.

    This can be due to network issues, timeouts, or HTTP errors from the server
    that are not covered by more specific exceptions like RateLimitError or NotFoundError.
    """
