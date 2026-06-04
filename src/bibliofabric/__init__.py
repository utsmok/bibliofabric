"""Bibliofabric: Generic framework for building modern asynchronous API clients.

This package provides the core infrastructure for building bibliometric and scholarly
data retrieval clients. It includes generic HTTP client functionality, authentication
strategies, caching, rate limiting, and reusable resource mixins.

The framework is designed to be extended by specific API client implementations
(like aireloom for OpenAIRE) while centralizing common functionality.
"""

try:
    from importlib.metadata import PackageNotFoundError, version as _get_version

    __version__ = _get_version("bibliofabric")
except PackageNotFoundError:
    __version__ = "0.0.0"
__author__ = "Samuel Mok"
__email__ = "s.mok@utwente.nl"

from .auth import AuthStrategy, ClientCredentialsAuth, NoAuth, StaticTokenAuth
from .client import BaseApiClient
from .config import BaseApiSettings
from .exceptions import (
    APIError,
    AuthError,
    BibliofabricError,
    BibliofabricRequestError,
    ConfigurationError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)
from .models import ResponseUnwrapper
from .resources import (
    BaseResourceClient,
    CursorIterableMixin,
    GettableMixin,
    PageIterableMixin,
    SearchableMixin,
)

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "AuthStrategy",
    "BaseApiClient",
    "BaseApiSettings",
    "BaseResourceClient",
    "BibliofabricError",
    "APIError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "TimeoutError",
    "NetworkError",
    "ConfigurationError",
    "AuthError",
    "BibliofabricRequestError",
    "ClientCredentialsAuth",
    "CursorIterableMixin",
    "GettableMixin",
    "NoAuth",
    "PageIterableMixin",
    "ResponseUnwrapper",
    "SearchableMixin",
    "StaticTokenAuth",
]
