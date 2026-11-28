"""opcitato: Python interface for the OpenCitations Index and Meta APIs."""

try:
    from importlib.metadata import PackageNotFoundError, version as _get_version

    __version__ = _get_version("opcitato")
except PackageNotFoundError:
    __version__ = "0.0.0"

from bibliofabric.exceptions import (
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

from ._async.client import OpcitatoClient
from ._async.resources import IndexClient, MetaClient
from ._sync.client import OpcitatoSyncClient
from ._sync.resources import IndexSyncClient, MetaSyncClient
from .config import OpcitatoSettings, get_settings
from .csvparse import parse_csv_rows
from .ids import (
    ParsedIdentifier,
    normalize_index_id,
    normalize_issn,
    normalize_meta_ids,
    normalize_oci,
    normalize_person_id,
    parse_identifiers,
)
from .models import Citation, Count, MetadataRecord, SparqlResult, SparqlTerm

__all__ = [
    "__version__",
    "APIError",
    "AuthError",
    "BibliofabricError",
    "Citation",
    "ConfigurationError",
    "Count",
    "IndexClient",
    "IndexSyncClient",
    "MetaClient",
    "MetadataRecord",
    "MetaSyncClient",
    "NetworkError",
    "NotFoundError",
    "OpcitatoClient",
    "OpcitatoSettings",
    "OpcitatoSyncClient",
    "ParsedIdentifier",
    "RateLimitError",
    "SparqlResult",
    "SparqlTerm",
    "TimeoutError",
    "ValidationError",
    "get_settings",
    "normalize_index_id",
    "normalize_issn",
    "normalize_meta_ids",
    "normalize_oci",
    "normalize_person_id",
    "parse_csv_rows",
    "parse_identifiers",
]
