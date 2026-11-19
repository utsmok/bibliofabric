"""Aletheca: Python interface for the OpenAlex API."""

try:
    from importlib.metadata import PackageNotFoundError, version as _get_version

    __version__ = _get_version("aletheca")
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

from ._async.authors import AuthorsClient
from ._async.awards import AwardsClient
from ._async.client import AlethecaClient
from ._async.funders import FundersClient
from ._async.institutions import InstitutionsClient
from ._async.keywords import KeywordsClient
from ._async.links import LinksClient
from ._async.locations import LocationsClient
from ._async.publishers import PublishersClient
from ._async.sources import SourcesClient
from ._async.topics import TopicsClient
from ._async.works import WorksClient
from ._sync.authors import AuthorsSyncClient
from ._sync.awards import AwardsSyncClient
from ._sync.client import AlethecaSyncClient
from ._sync.funders import FundersSyncClient
from ._sync.institutions import InstitutionsSyncClient
from ._sync.keywords import KeywordsSyncClient
from ._sync.links import LinksSyncClient
from ._sync.locations import LocationsSyncClient
from ._sync.publishers import PublishersSyncClient
from ._sync.sources import SourcesSyncClient
from ._sync.topics import TopicsSyncClient
from ._sync.works import WorksSyncClient
from .config import AlethecaSettings
from .filters import (
    AuthorsFilters,
    AwardsFilters,
    FundersFilters,
    InstitutionsFilters,
    KeywordsFilters,
    PublishersFilters,
    SourcesFilters,
    TopicsFilters,
    WorksFilters,
)
from .models import (
    Author,
    AutocompleteResult,
    Award,
    BaseEntity,
    Funder,
    GroupByBucket,
    Institution,
    Keyword,
    Link,
    LocationRecord,
    Publisher,
    RateLimitStatus,
    Source,
    Topic,
    Work,
)

__all__ = [
    "__version__",
    "AlethecaClient",
    "AlethecaSettings",
    "AlethecaSyncClient",
    "APIError",
    "AuthError",
    "Author",
    "AuthorsClient",
    "AuthorsFilters",
    "AuthorsSyncClient",
    "AutocompleteResult",
    "Award",
    "AwardsClient",
    "AwardsFilters",
    "AwardsSyncClient",
    "BaseEntity",
    "BibliofabricError",
    "ConfigurationError",
    "Funder",
    "FundersClient",
    "FundersFilters",
    "FundersSyncClient",
    "GroupByBucket",
    "Institution",
    "InstitutionsClient",
    "InstitutionsFilters",
    "InstitutionsSyncClient",
    "Keyword",
    "KeywordsClient",
    "KeywordsFilters",
    "KeywordsSyncClient",
    "Link",
    "LinksClient",
    "LinksSyncClient",
    "LocationRecord",
    "LocationsClient",
    "LocationsSyncClient",
    "NetworkError",
    "NotFoundError",
    "Page",
    "Publisher",
    "PublishersClient",
    "PublishersFilters",
    "PublishersSyncClient",
    "RateLimitError",
    "RateLimitStatus",
    "Source",
    "SourcesClient",
    "SourcesFilters",
    "SourcesSyncClient",
    "TimeoutError",
    "Topic",
    "TopicsClient",
    "TopicsFilters",
    "TopicsSyncClient",
    "ValidationError",
    "Work",
    "WorksClient",
    "WorksFilters",
    "WorksSyncClient",
]
