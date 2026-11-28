"""prodromus: Python interface for the bioRxiv and medRxiv API."""

try:
    from importlib.metadata import PackageNotFoundError, version as _get_version

    __version__ = _get_version("prodromus")
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

from ._async.client import ProdromusClient
from ._async.routes import (
    DetailsClient,
    FundersClient,
    PublishedClient,
    StatisticsClient,
)
from ._sync.client import ProdromusSyncClient
from ._sync.routes import (
    DetailsSyncClient,
    FundersSyncClient,
    PublishedSyncClient,
    StatisticsSyncClient,
)
from .config import ProdromusSettings, get_settings
from .dialect import (
    BIORXIV_API_BASE_URL,
    DETAILS_PAGE_SIZE,
    PUBLISHED_PAGE_SIZE,
    SERVERS,
)
from .models import (
    ContentStatistic,
    FunderDeclaration,
    Preprint,
    PublishedArticle,
    UsageStatistic,
)
from .unwrapper import ProdromusUnwrapper

__all__ = [
    "APIError",
    "AuthError",
    "BIORXIV_API_BASE_URL",
    "BibliofabricError",
    "ConfigurationError",
    "ContentStatistic",
    "DETAILS_PAGE_SIZE",
    "DetailsClient",
    "DetailsSyncClient",
    "FunderDeclaration",
    "FundersClient",
    "FundersSyncClient",
    "NetworkError",
    "NotFoundError",
    "PUBLISHED_PAGE_SIZE",
    "Page",
    "Preprint",
    "ProdromusClient",
    "ProdromusSettings",
    "ProdromusSyncClient",
    "ProdromusUnwrapper",
    "PublishedArticle",
    "PublishedClient",
    "PublishedSyncClient",
    "RateLimitError",
    "SERVERS",
    "StatisticsClient",
    "StatisticsSyncClient",
    "TimeoutError",
    "UsageStatistic",
    "ValidationError",
    "__version__",
    "get_settings",
]
