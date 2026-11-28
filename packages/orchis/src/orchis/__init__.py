"""orchis: Python interface for the ORCID Public API v3.0."""

try:
    from importlib.metadata import PackageNotFoundError, version as _get_version

    __version__ = _get_version("orchis")
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

from ._async.client import OrchisClient
from ._async.resources import (
    ActivitiesClient,
    ExpandedSearchClient,
    PersonClient,
    RecordClient,
    SolrSearchClient,
)
from ._sync.client import OrchisSyncClient
from ._sync.resources import (
    ActivitiesSyncClient,
    ExpandedSearchSyncClient,
    PersonSyncClient,
    RecordSyncClient,
    SolrSearchSyncClient,
)
from .config import OrchisSettings, get_settings
from .dialect import (
    DEFAULT_SEARCH_ROWS,
    EXPANDED_SEARCH_MAX_ROWS,
    ORCID_API_BASE_URL,
)
from .models import (
    ActivitiesSummary,
    Biography,
    Email,
    ExpandedResult,
    ExternalIdentifiers,
    Funding,
    FuzzyDate,
    History,
    OrchisRecord,
    Person,
    PersonalDetails,
    ResearcherUrls,
    SolrResult,
    TextValue,
    Work,
    WorksSection,
    text,
)
from .unwrapper import OrchisUnwrapper

__all__ = [
    "__version__",
    "ActivitiesClient",
    "ActivitiesSummary",
    "ActivitiesSyncClient",
    "APIError",
    "AuthError",
    "Biography",
    "BibliofabricError",
    "ConfigurationError",
    "DEFAULT_SEARCH_ROWS",
    "Email",
    "ExpandedResult",
    "FuzzyDate",
    "ExpandedSearchClient",
    "EXPANDED_SEARCH_MAX_ROWS",
    "ExpandedSearchSyncClient",
    "ExternalIdentifiers",
    "Funding",
    "get_settings",
    "History",
    "NetworkError",
    "NotFoundError",
    "ORCID_API_BASE_URL",
    "Page",
    "Person",
    "PersonClient",
    "PersonalDetails",
    "PersonSyncClient",
    "RateLimitError",
    "RecordClient",
    "RecordSyncClient",
    "ResearcherUrls",
    "SolrResult",
    "TextValue",
    "SolrSearchClient",
    "SolrSearchSyncClient",
    "OrchisClient",
    "OrchisRecord",
    "OrchisSettings",
    "OrchisSyncClient",
    "OrchisUnwrapper",
    "text",
    "TimeoutError",
    "ValidationError",
    "Work",
    "WorksSection",
]
