"""Stavrophora: Python interface for the Crossref API."""

try:
    from importlib.metadata import PackageNotFoundError, version as _get_version

    __version__ = _get_version("stavrophora")
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

from ._async.client import StavrophoraClient
from ._async.dialect import CrossrefResourceClient
from ._async.funders import FundersResource, FunderWorksResource
from ._async.journals import JournalsResource
from ._async.licenses import LicensesResource
from ._async.members import MembersResource
from ._async.prefixes import PrefixesResource
from ._async.types import TypesResource
from ._async.works import ScopedWorksResource, WorksResource
from ._sync.client import StavrophoraSyncClient
from ._sync.dialect import CrossrefResourceSyncClient
from ._sync.funders import SyncFundersResource, SyncFunderWorksResource
from ._sync.journals import SyncJournalsResource
from ._sync.licenses import SyncLicensesResource
from ._sync.members import SyncMembersResource
from ._sync.prefixes import SyncPrefixesResource
from ._sync.types import SyncTypesResource
from ._sync.works import SyncScopedWorksResource, SyncWorksResource
from .config import StavrophoraSettings, get_settings
from .filters import FunderFilters, MemberFilters, WorksFilters
from .models import (
    Agency,
    Contributor,
    CrossRefDate,
    CrossRefType,
    Funder,
    FunderRef,
    IssnType,
    Journal,
    License,
    LicenseRef,
    Member,
    Prefix,
    Work,
    WorkAgency,
)

__all__ = [
    "__version__",
    "Agency",
    "APIError",
    "AuthError",
    "BibliofabricError",
    "ConfigurationError",
    "Contributor",
    "CrossRefDate",
    "CrossRefType",
    "CrossrefResourceClient",
    "CrossrefResourceSyncClient",
    "Funder",
    "FunderFilters",
    "FunderRef",
    "FunderWorksResource",
    "FundersResource",
    "get_settings",
    "IssnType",
    "Journal",
    "License",
    "LicenseRef",
    "Member",
    "MemberFilters",
    "MembersResource",
    "NetworkError",
    "NotFoundError",
    "Page",
    "Prefix",
    "PrefixesResource",
    "RateLimitError",
    "ScopedWorksResource",
    "StavrophoraClient",
    "StavrophoraSettings",
    "StavrophoraSyncClient",
    "SyncFunderWorksResource",
    "SyncFundersResource",
    "SyncJournalsResource",
    "SyncLicensesResource",
    "SyncMembersResource",
    "SyncPrefixesResource",
    "SyncScopedWorksResource",
    "SyncTypesResource",
    "SyncWorksResource",
    "TimeoutError",
    "TypesResource",
    "ValidationError",
    "Work",
    "WorkAgency",
    "WorksFilters",
    "WorksResource",
]
