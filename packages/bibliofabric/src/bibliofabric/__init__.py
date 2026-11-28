"""bibliofabric: shared core for scholarly API client libraries.

The framework owns HTTP, auth, retries, throttling, error mapping, paging,
batch retrieval, identifier normalization, and typed resource clients. Concrete
client libraries supply the API-specific settings, dialect, unwrapper, models,
and resource subclasses.
"""

from importlib.metadata import PackageNotFoundError, version as _package_version

try:
    __version__ = _package_version("bibliofabric")
except PackageNotFoundError:
    __version__ = "0.0.0"
__author__ = "Samuel Mok"
__email__ = "s.mok@utwente.nl"

from ._async.client import BaseApiClient
from ._async.resources import OnError, ResourceClient
from ._sync.client import SyncBaseApiClient
from ._sync.resources import SyncResourceClient
from .auth import (
    AuthStrategy,
    BasicAuth,
    ClientCredentialsAuth,
    HeaderAuth,
    NoAuth,
    QueryParameterAuth,
    RefreshTokenAuth,
    StaticTokenAuth,
)
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
    validate_model,
)
from .ids import (
    is_doi,
    normalize_arxiv,
    normalize_doi,
    normalize_gnd,
    normalize_isbn,
    normalize_isni,
    normalize_issn,
    normalize_orcid,
    normalize_pmcid,
    normalize_pmid,
    normalize_ror,
    normalize_viaf,
    normalize_wikidata_qid,
    strip_url_prefix,
)
from .paging import Page, QueryDialect
from .types import SafeList, SafeStr
from .unwrap import JsonApiUnwrapper, ResponseUnwrapper

__all__ = [
    "__author__",
    "__email__",
    "__version__",
    "APIError",
    "AuthError",
    "AuthStrategy",
    "BaseApiClient",
    "BaseApiSettings",
    "BasicAuth",
    "BibliofabricError",
    "ClientCredentialsAuth",
    "ConfigurationError",
    "HeaderAuth",
    "JsonApiUnwrapper",
    "NetworkError",
    "NoAuth",
    "NotFoundError",
    "OnError",
    "Page",
    "QueryDialect",
    "QueryParameterAuth",
    "RateLimitError",
    "RefreshTokenAuth",
    "ResourceClient",
    "ResponseUnwrapper",
    "SafeList",
    "SafeStr",
    "StaticTokenAuth",
    "SyncBaseApiClient",
    "SyncResourceClient",
    "TimeoutError",
    "ValidationError",
    "is_doi",
    "normalize_arxiv",
    "normalize_doi",
    "normalize_gnd",
    "normalize_isbn",
    "normalize_isni",
    "normalize_issn",
    "normalize_orcid",
    "normalize_pmcid",
    "normalize_pmid",
    "normalize_ror",
    "normalize_viaf",
    "normalize_wikidata_qid",
    "strip_url_prefix",
    "validate_model",
]
