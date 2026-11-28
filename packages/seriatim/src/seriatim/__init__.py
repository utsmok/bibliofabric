"""seriatim: Python interface for the ISSN Portal."""

try:
    from importlib.metadata import PackageNotFoundError, version as _get_version

    __version__ = _get_version("seriatim")
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

from ._async.client import SeriatimClient
from ._async.ltwa import LtwaClient
from ._async.resources import IssnLClient, RecordsClient
from ._async.search import SearchClient
from ._sync.client import SeriatimSyncClient
from ._sync.ltwa import LtwaSyncClient
from ._sync.resources import IssnLSyncClient, RecordsSyncClient
from ._sync.search import SearchSyncClient
from .config import SeriatimSettings, get_settings
from .filters import is_valid_issn, require_issn
from .issn_l_table import IssnLink, iter_issn_l_clusters, iter_issn_to_issn_l
from .ltwa_parser import parse_ltwa_page
from .models import (
    GenerationActivity,
    HasPart,
    IdentifiedBy,
    IsPartOf,
    IssnLRecord,
    LangString,
    LtwaEntry,
    LtwaPage,
    OtherMedium,
    RecordAttribution,
    RecordProvenance,
    SearchHit,
    SearchPage,
    SeriatimRecord,
    TitleValue,
)
from .parser import parse_issn_l, parse_issn_record, record_issn
from .search_parser import parse_search_page

__all__ = [
    "__version__",
    "APIError",
    "AuthError",
    "BibliofabricError",
    "ConfigurationError",
    "GenerationActivity",
    "HasPart",
    "IdentifiedBy",
    "IsPartOf",
    "IssnLClient",
    "IssnLRecord",
    "IssnLSyncClient",
    "IssnLink",
    "iter_issn_l_clusters",
    "iter_issn_to_issn_l",
    "is_valid_issn",
    "LangString",
    "LtwaClient",
    "LtwaEntry",
    "LtwaPage",
    "LtwaSyncClient",
    "NetworkError",
    "NotFoundError",
    "OtherMedium",
    "Page",
    "parse_issn_l",
    "parse_issn_record",
    "parse_ltwa_page",
    "parse_search_page",
    "RateLimitError",
    "RecordAttribution",
    "RecordProvenance",
    "RecordsClient",
    "RecordsSyncClient",
    "record_issn",
    "require_issn",
    "SearchClient",
    "SearchHit",
    "SearchPage",
    "SearchSyncClient",
    "TimeoutError",
    "TitleValue",
    "SeriatimClient",
    "SeriatimRecord",
    "SeriatimSettings",
    "SeriatimSyncClient",
    "ValidationError",
    "get_settings",
]
