"""diurnalia: Python interface for the DOAJ API v4."""

try:
    from importlib.metadata import PackageNotFoundError, version as _get_version

    __version__ = _get_version("diurnalia")
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

from ._async.articles import ArticlesClient
from ._async.base import DiurnaliaResourceClient, quote_query
from ._async.client import DiurnaliaClient
from ._async.journals import JournalsClient
from ._sync.articles import ArticlesSyncClient
from ._sync.base import DiurnaliaResourceSyncClient
from ._sync.client import DiurnaliaSyncClient
from ._sync.journals import JournalsSyncClient
from .config import DiurnaliaSettings, get_settings
from .dialect import (
    DOAJ_API_BASE_URL,
    DOAJ_DEFAULT_PAGE_SIZE,
    DOAJ_DIALECT,
    DOAJ_ITERATE_PAGE_SIZE,
    DOAJ_MAX_OFFSET,
    DOAJ_MAX_PAGE_SIZE,
)
from .filters import doi_query, issn_query
from .models import (
    Admin,
    Apc,
    Article,
    ArticleBibjson,
    ArticleDisplay,
    ArticleJournal,
    Author,
    Copyright,
    DepositPolicy,
    Editorial,
    Identifier,
    Journal,
    JournalBibjson,
    JournalPublisher,
    License,
    Link,
    OtherCharges,
    PidScheme,
    Plagiarism,
    Preservation,
    Price,
    Ref,
    Subject,
    Waiver,
)
from .unwrapper import DiurnaliaUnwrapper

__all__ = [
    "Admin",
    "APIError",
    "Apc",
    "Article",
    "ArticleBibjson",
    "ArticleDisplay",
    "ArticleJournal",
    "ArticlesClient",
    "ArticlesSyncClient",
    "AuthError",
    "Author",
    "BibliofabricError",
    "ConfigurationError",
    "Copyright",
    "DOAJ_API_BASE_URL",
    "DOAJ_DEFAULT_PAGE_SIZE",
    "DOAJ_DIALECT",
    "DOAJ_ITERATE_PAGE_SIZE",
    "DOAJ_MAX_OFFSET",
    "DOAJ_MAX_PAGE_SIZE",
    "DepositPolicy",
    "Editorial",
    "Identifier",
    "Journal",
    "JournalBibjson",
    "JournalPublisher",
    "JournalsClient",
    "JournalsSyncClient",
    "License",
    "Link",
    "NetworkError",
    "NotFoundError",
    "OtherCharges",
    "Page",
    "PidScheme",
    "Plagiarism",
    "Preservation",
    "Price",
    "RateLimitError",
    "Ref",
    "Subject",
    "DiurnaliaResourceSyncClient",
    "DiurnaliaClient",
    "DiurnaliaResourceClient",
    "DiurnaliaSettings",
    "DiurnaliaSyncClient",
    "DiurnaliaUnwrapper",
    "TimeoutError",
    "ValidationError",
    "Waiver",
    "__version__",
    "doi_query",
    "get_settings",
    "issn_query",
    "quote_query",
]
