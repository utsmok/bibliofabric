"""hodoi: Python interface for the DOI System proxy at doi.org."""

try:
    from importlib.metadata import PackageNotFoundError, version as _get_version

    __version__ = _get_version("hodoi")
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

from ._async.client import HodoiClient
from ._sync.client import HodoiSyncClient
from .config import (
    DEFAULT_MAX_CONCURRENCY,
    DEFAULT_MAX_REQUESTS_PER_SECOND,
    DEFAULT_TIMEOUT,
    HodoiSettings,
    get_settings,
)
from .dialect import (
    DOI_BASE_URL,
    RA_BATCH_SIZE,
    RA_MAX_PATH_CHARS,
    doi_path,
    normalize_doi,
    ra_chunks,
    strip_doi_form,
)
from .media_types import (
    AGENCY_SUPPORT,
    BIBLIOGRAPHY,
    BIBTEX,
    CSL_JSON,
    DATACITE_JSON,
    DATACITE_XML,
    JSON_MEDIA_TYPES,
    MEDIA_TYPES,
    ONIX_DOI_XML,
    RDF_XML,
    RIS,
    SCHEMAORG_JSONLD,
    TURTLE,
    UNIXREF_XML,
    UNIXSD_XML,
)
from .models import (
    AgencyAnswer,
    CslItem,
    DataciteRecord,
    HandleAdminValue,
    HandleRecord,
    HandleValue,
    HandleValueData,
    RedirectLocation,
    SchemaOrgThing,
)
from .xmlparse import parse_locations

__all__ = [
    "__version__",
    "AGENCY_SUPPORT",
    "APIError",
    "AgencyAnswer",
    "AuthError",
    "BIBLIOGRAPHY",
    "BIBTEX",
    "BibliofabricError",
    "CSL_JSON",
    "ConfigurationError",
    "CslItem",
    "DATACITE_JSON",
    "DATACITE_XML",
    "DEFAULT_MAX_CONCURRENCY",
    "DEFAULT_MAX_REQUESTS_PER_SECOND",
    "DEFAULT_TIMEOUT",
    "DOI_BASE_URL",
    "DataciteRecord",
    "HandleAdminValue",
    "HandleRecord",
    "HandleValue",
    "HandleValueData",
    "HodoiClient",
    "HodoiSettings",
    "HodoiSyncClient",
    "JSON_MEDIA_TYPES",
    "MEDIA_TYPES",
    "NetworkError",
    "NotFoundError",
    "ONIX_DOI_XML",
    "RA_BATCH_SIZE",
    "RA_MAX_PATH_CHARS",
    "RDF_XML",
    "RIS",
    "RateLimitError",
    "RedirectLocation",
    "SCHEMAORG_JSONLD",
    "SchemaOrgThing",
    "TimeoutError",
    "TURTLE",
    "UNIXREF_XML",
    "UNIXSD_XML",
    "ValidationError",
    "doi_path",
    "get_settings",
    "normalize_doi",
    "parse_locations",
    "ra_chunks",
    "strip_doi_form",
]
