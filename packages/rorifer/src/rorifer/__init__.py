"""rorifer: Python interface for the ROR API v2."""

try:
    from importlib.metadata import PackageNotFoundError, version as _get_version

    __version__ = _get_version("rorifer")
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

from ._async.client import RoriferClient
from ._async.dialect import serialize_filter_params
from ._async.dumps import DumpsClient
from ._async.organizations import OrganizationsClient
from ._sync.client import RoriferSyncClient
from ._sync.dumps import DumpsSyncClient
from ._sync.organizations import OrganizationsSyncClient
from .config import RoriferSettings, get_settings
from .crosswalk import FUNDREF_DOI_PREFIX, fundref_doi_from_id, fundref_id_from_doi
from .dump import compact_external_id, index_external_ids, iter_dump_records
from .filters import OrganizationFilters
from .models import (
    Admin,
    AdminDate,
    AffiliationMatch,
    DumpFile,
    DumpFileLinks,
    DumpLinks,
    DumpMetadata,
    ExternalId,
    FacetCount,
    GeonamesDetails,
    Link,
    Location,
    Name,
    Organization,
    Relationship,
    RorDump,
)

__all__ = [
    "__version__",
    "Admin",
    "AdminDate",
    "AffiliationMatch",
    "APIError",
    "AuthError",
    "BibliofabricError",
    "compact_external_id",
    "ConfigurationError",
    "DumpsClient",
    "DumpsSyncClient",
    "DumpFile",
    "DumpFileLinks",
    "DumpLinks",
    "DumpMetadata",
    "external_id_query",
    "ExternalId",
    "FacetCount",
    "FUNDREF_DOI_PREFIX",
    "fundref_doi_from_id",
    "fundref_id_from_doi",
    "get_settings",
    "GeonamesDetails",
    "index_external_ids",
    "iter_dump_records",
    "Link",
    "Location",
    "Name",
    "NetworkError",
    "NotFoundError",
    "Organization",
    "OrganizationsClient",
    "OrganizationsSyncClient",
    "OrganizationFilters",
    "Page",
    "RateLimitError",
    "Relationship",
    "RorDump",
    "serialize_filter_params",
    "RoriferClient",
    "RoriferSettings",
    "RoriferSyncClient",
    "TimeoutError",
    "ValidationError",
]
