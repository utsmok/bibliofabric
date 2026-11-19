"""bibliofabric: shared core for scholarly API client libraries.

The framework owns HTTP, auth, retries, throttling, error mapping, paging,
batch retrieval, identifier normalization, and typed resource clients. Concrete
client libraries (aireloom, aletheca, stavrophora) supply the API-specific
settings, dialect, unwrapper, models, and resource subclasses.
"""

from importlib.metadata import PackageNotFoundError, version as _package_version

try:
    __version__ = _package_version("bibliofabric")
except PackageNotFoundError:
    __version__ = "0.0.0"
__author__ = "Samuel Mok"
__email__ = "s.mok@utwente.nl"

from .auth import (
    AuthStrategy,
    ClientCredentialsAuth,
    HeaderAuth,
    NoAuth,
    QueryParameterAuth,
    StaticTokenAuth,
)
from .client import BaseApiClient
from .config import BaseApiSettings
from .exceptions import (
    APIError,
    AuthError,
    BibliofabricError,
    ConfigurationError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)
from .ids import (
    is_doi,
    normalize_doi,
    normalize_issn,
    normalize_orcid,
    normalize_ror,
    strip_url_prefix,
)
from .paging import Page, QueryDialect
from .resources import ResourceClient
from .types import SafeList, SafeStr
from .unwrap import ResponseUnwrapper

__all__ = [
    "__author__",
    "__email__",
    "__version__",
    "APIError",
    "AuthError",
    "AuthStrategy",
    "BaseApiClient",
    "BaseApiSettings",
    "BibliofabricError",
    "ClientCredentialsAuth",
    "ConfigurationError",
    "HeaderAuth",
    "NetworkError",
    "NoAuth",
    "NotFoundError",
    "Page",
    "QueryDialect",
    "RateLimitError",
    "ResourceClient",
    "ResponseUnwrapper",
    "SafeList",
    "SafeStr",
    "StaticTokenAuth",
    "TimeoutError",
    "ValidationError",
    "is_doi",
    "normalize_doi",
    "normalize_issn",
    "normalize_orcid",
    "normalize_ror",
    "strip_url_prefix",
]
