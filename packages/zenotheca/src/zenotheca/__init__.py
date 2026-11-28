"""zenotheca: Python interface for the Zenodo REST API."""

try:
    from importlib.metadata import PackageNotFoundError, version as _get_version

    __version__ = _get_version("zenotheca")
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

from ._async.client import ZenothecaClient
from ._async.communities import ZenothecaCommunitiesClient
from ._async.oai import OaiClient
from ._async.records import ZenothecaRecordsClient
from ._async.vocabularies import VocabulariesClient
from ._sync.client import ZenothecaSyncClient
from ._sync.communities import ZenothecaCommunitiesSyncClient
from ._sync.oai import OaiSyncClient
from ._sync.records import ZenothecaRecordsSyncClient
from ._sync.vocabularies import VocabulariesSyncClient
from .config import ZenothecaSettings, get_settings
from .dialect import (
    RECORD_EXPORT_FORMATS,
    RECORD_SORT_OPTIONS,
    TOP_LEVEL_VOCABULARIES,
    ZENODO_API_BASE_URL,
    ZENODO_DEFAULT_PAGE_SIZE,
    ZENODO_MAX_PAGE_SIZE,
    ZENODO_MAX_RESULT_WINDOW,
    ZENODO_OAI_BASE_URL,
)
from .filters import all_of, any_of, community, phrase, resource_type, term
from .ids import normalize_community_slug, normalize_record_id
from .models import (
    ZenothecaCommunity,
    ZenothecaCommunityMetadata,
    ZenothecaCommunityOrganization,
    ZenothecaCommunityRef,
    ZenothecaCommunityType,
    ZenothecaContributor,
    ZenothecaCreator,
    ZenothecaDate,
    ZenothecaDeletionStatus,
    ZenothecaFile,
    ZenothecaFileEntry,
    ZenothecaFiles,
    ZenothecaLicense,
    ZenothecaOwner,
    ZenothecaRecord,
    ZenothecaRecordMetadata,
    ZenothecaRelatedIdentifier,
    ZenothecaRelations,
    ZenothecaResourceType,
    ZenothecaStats,
    ZenothecaVersionInfo,
)

__all__ = [
    "APIError",
    "AuthError",
    "BibliofabricError",
    "ConfigurationError",
    "NetworkError",
    "NotFoundError",
    "Page",
    "RECORD_EXPORT_FORMATS",
    "RECORD_SORT_OPTIONS",
    "TOP_LEVEL_VOCABULARIES",
    "RateLimitError",
    "TimeoutError",
    "OaiClient",
    "OaiSyncClient",
    "ZenothecaClient",
    "ZenothecaCommunitiesClient",
    "ZenothecaCommunitiesSyncClient",
    "ZenothecaCommunity",
    "ZenothecaCommunityMetadata",
    "ZenothecaCommunityOrganization",
    "ZenothecaCommunityRef",
    "ZenothecaCommunityType",
    "ZenothecaContributor",
    "ZenothecaCreator",
    "ZenothecaDate",
    "ZenothecaDeletionStatus",
    "ZenothecaFile",
    "ZenothecaFileEntry",
    "ZenothecaFiles",
    "ZenothecaLicense",
    "ZenothecaOwner",
    "ZenothecaRecord",
    "ZenothecaRecordMetadata",
    "ZenothecaRecordsClient",
    "ZenothecaRecordsSyncClient",
    "ZenothecaRelatedIdentifier",
    "ZenothecaRelations",
    "ZenothecaResourceType",
    "ZenothecaSettings",
    "ZenothecaStats",
    "ZenothecaSyncClient",
    "ZenothecaVersionInfo",
    "VocabulariesClient",
    "VocabulariesSyncClient",
    "ValidationError",
    "ZENODO_API_BASE_URL",
    "ZENODO_DEFAULT_PAGE_SIZE",
    "ZENODO_MAX_PAGE_SIZE",
    "ZENODO_MAX_RESULT_WINDOW",
    "ZENODO_OAI_BASE_URL",
    "all_of",
    "any_of",
    "community",
    "get_settings",
    "normalize_community_slug",
    "normalize_record_id",
    "phrase",
    "resource_type",
    "term",
    "__version__",
]
