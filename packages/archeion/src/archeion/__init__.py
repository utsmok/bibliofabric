"""archeion: Python interface for the arXiv API."""

try:
    from importlib.metadata import PackageNotFoundError, version as _get_version

    __version__ = _get_version("archeion")
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

from ._async.client import ArcheionClient
from ._async.query import QueryClient
from ._sync.client import ArcheionSyncClient
from ._sync.query import QuerySyncClient
from .atom import parse_feed
from .config import ArcheionSettings, get_settings
from .dialect import (
    ARXIV_API_BASE_URL,
    DEFAULT_PAGE_SIZE,
    MAX_RESULTS_PER_PAGE,
    MAX_TOTAL_RESULTS,
    SORT_BY,
    SORT_ORDER,
)
from .models import ArxivAuthor, ArxivEntry, ArxivLink
from .unwrapper import ArcheionUnwrapper

__all__ = [
    "ARXIV_API_BASE_URL",
    "APIError",
    "ArcheionClient",
    "ArcheionSettings",
    "ArcheionSyncClient",
    "ArcheionUnwrapper",
    "ArxivAuthor",
    "ArxivEntry",
    "ArxivLink",
    "AuthError",
    "BibliofabricError",
    "ConfigurationError",
    "DEFAULT_PAGE_SIZE",
    "MAX_RESULTS_PER_PAGE",
    "MAX_TOTAL_RESULTS",
    "NetworkError",
    "NotFoundError",
    "Page",
    "QueryClient",
    "QuerySyncClient",
    "RateLimitError",
    "SORT_BY",
    "SORT_ORDER",
    "TimeoutError",
    "ValidationError",
    "__version__",
    "get_settings",
    "parse_feed",
]
