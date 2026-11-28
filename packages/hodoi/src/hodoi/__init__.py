"""hodoi: Python interface for the DOI System proxy at doi.org."""

try:
    from importlib.metadata import PackageNotFoundError, version as _get_version

    __version__ = _get_version("hodoi")
except PackageNotFoundError:
    __version__ = "0.0.0"

from bibliofabric import Page
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
from .dialect import DOI_BASE_URL, RA_BATCH_SIZE, normalize_doi
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
    SchemaOrgThing,
)

__all__ = [
    "AGENCY_SUPPORT",
    "APIError",
    "AuthError",
    "AgencyAnswer",
    "BIBLIOGRAPHY",
    "BIBTEX",
    "BibliofabricError",
    "CSL_JSON",
    "ConfigurationError",
    "DATACITE_JSON",
    "DATACITE_XML",
    "DOI_BASE_URL",
    "DataciteRecord",
    "DEFAULT_MAX_CONCURRENCY",
    "DEFAULT_MAX_REQUESTS_PER_SECOND",
    "DEFAULT_TIMEOUT",
    "HandleAdminValue",
    "HandleRecord",
    "HandleValue",
    "HandleValueData",
    "JSON_MEDIA_TYPES",
    "MEDIA_TYPES",
    "NetworkError",
    "NotFoundError",
    "ONIX_DOI_XML",
    "Page",
    "RDF_XML",
    "RA_BATCH_SIZE",
    "RIS",
    "RateLimitError",
    "SCHEMAORG_JSONLD",
    "SchemaOrgThing",
    "TimeoutError",
    "TURTLE",
    "HodoiClient",
    "HodoiSettings",
    "HodoiSyncClient",
    "UNIXREF_XML",
    "UNIXSD_XML",
    "ValidationError",
    "CslItem",
    "get_settings",
    "normalize_doi",
]
