"""quiddita: Python interface for Wikidata's Action API, REST API, and SPARQL."""

try:
    from importlib.metadata import PackageNotFoundError, version as _get_version

    __version__ = _get_version("quiddita")
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

from ._async.claims import ClaimsClient
from ._async.client import QuidditaClient, QuidditaQueryClient
from ._async.entities import EntitiesClient
from ._async.entity_data import EntityDataClient
from ._async.lexemes import LexemesClient
from ._async.rest_items import ItemsClient, PropertiesClient
from ._async.search import SearchClient
from ._async.sitelinks import SitelinksClient
from ._async.sparql import SparqlClient
from ._async.statements import StatementsClient
from ._async.utilities import UtilitiesClient
from ._sync.claims import ClaimsSyncClient
from ._sync.client import QuidditaQuerySyncClient, QuidditaSyncClient
from ._sync.entities import EntitiesSyncClient
from ._sync.entity_data import EntityDataSyncClient
from ._sync.lexemes import LexemesSyncClient
from ._sync.rest_items import ItemsSyncClient, PropertiesSyncClient
from ._sync.search import SearchSyncClient
from ._sync.sitelinks import SitelinksSyncClient
from ._sync.sparql import SparqlSyncClient
from ._sync.statements import StatementsSyncClient
from ._sync.utilities import UtilitiesSyncClient
from .config import QuidditaSettings, get_settings
from .dialect import ACTION_PATH, MAX_IDS_PER_REQUEST, REST_PREFIX, SPARQL_BASE_URL
from .ids import normalize_wikidata_id
from .models import (
    CheckedClaim,
    Claim,
    ClaimsByProperty,
    Constraint,
    ConstraintCheckResult,
    ConstraintChecksByProperty,
    DataValue,
    Entity,
    EntityDataDocument,
    EntityDataResult,
    EntitySearchResult,
    MonolingualText,
    ParsedValue,
    PropertySuggestion,
    Reference,
    RestItem,
    RestLexeme,
    RestLexemeForm,
    RestLexemeSense,
    RestProperty,
    RestQualifier,
    RestQualifierProperty,
    RestReference,
    RestReferenceValue,
    RestSearchResult,
    RestSitelink,
    RestStatement,
    RestTerm,
    RestTermResponse,
    Sitelink,
    Snak,
    SparqlBinding,
    SparqlBindingValue,
    SparqlHead,
    SparqlResult,
    SparqlResults,
    StatementsByProperty,
    Term,
)
from .unwrapper import QuidditaUnwrapper

__all__ = [
    "__version__",
    "ACTION_PATH",
    "APIError",
    "AuthError",
    "BibliofabricError",
    "Claim",
    "ClaimsByProperty",
    "ClaimsClient",
    "CheckedClaim",
    "ClaimsSyncClient",
    "ConfigurationError",
    "Constraint",
    "ConstraintCheckResult",
    "ConstraintChecksByProperty",
    "DataValue",
    "EntitiesClient",
    "EntitiesSyncClient",
    "Entity",
    "EntityDataClient",
    "EntityDataDocument",
    "EntityDataResult",
    "EntityDataSyncClient",
    "EntitySearchResult",
    "ItemsClient",
    "ItemsSyncClient",
    "LexemesClient",
    "LexemesSyncClient",
    "MAX_IDS_PER_REQUEST",
    "MonolingualText",
    "NetworkError",
    "normalize_wikidata_id",
    "NotFoundError",
    "Page",
    "ParsedValue",
    "PropertySuggestion",
    "PropertiesClient",
    "PropertiesSyncClient",
    "RateLimitError",
    "Reference",
    "REST_PREFIX",
    "RestItem",
    "RestLexeme",
    "RestLexemeForm",
    "RestLexemeSense",
    "RestProperty",
    "RestQualifier",
    "RestQualifierProperty",
    "RestReference",
    "RestReferenceValue",
    "RestSearchResult",
    "RestSitelink",
    "RestStatement",
    "RestTerm",
    "RestTermResponse",
    "SearchClient",
    "SearchSyncClient",
    "Sitelink",
    "SitelinksClient",
    "SitelinksSyncClient",
    "Snak",
    "SPARQL_BASE_URL",
    "SparqlBinding",
    "SparqlBindingValue",
    "SparqlClient",
    "SparqlHead",
    "SparqlResult",
    "SparqlResults",
    "SparqlSyncClient",
    "StatementsByProperty",
    "StatementsClient",
    "StatementsSyncClient",
    "QuidditaClient",
    "QuidditaQueryClient",
    "QuidditaQuerySyncClient",
    "QuidditaSettings",
    "QuidditaSyncClient",
    "QuidditaUnwrapper",
    "Term",
    "UtilitiesClient",
    "UtilitiesSyncClient",
    "TimeoutError",
    "ValidationError",
]
