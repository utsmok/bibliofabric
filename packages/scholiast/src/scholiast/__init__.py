"""scholiast: Python interface for the Semantic Scholar APIs."""

try:
    from importlib.metadata import PackageNotFoundError, version as _get_version

    __version__ = _get_version("scholiast")
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
from ._async.client import ScholiastClient
from ._async.datasets import DatasetsClient
from ._async.papers import PapersClient
from ._async.patents import PatentsClient
from ._async.recommendations import RecommendationsClient
from ._async.resources import ScholiastResourceClient
from ._async.snippets import SnippetsClient
from ._sync.authors import AuthorsSyncClient
from ._sync.client import ScholiastSyncClient
from ._sync.datasets import DatasetsSyncClient
from ._sync.papers import PapersSyncClient
from ._sync.patents import PatentsSyncClient
from ._sync.recommendations import RecommendationsSyncClient
from ._sync.resources import ScholiastResourceSyncClient
from ._sync.snippets import SnippetsSyncClient
from .config import ScholiastSettings, get_settings
from .dialect import (
    AUTHOR_BATCH_MAX_IDS,
    BULK_SEARCH_MAX_LIMIT,
    PAPER_BATCH_MAX_IDS,
    PAPER_SEARCH_MAX_LIMIT,
    SEARCH_MAX_OFFSET,
    SEMANTICSCHOLAR_DATASETS_BASE_URL,
    SEMANTICSCHOLAR_DIALECT,
    SEMANTICSCHOLAR_GRAPH_BASE_URL,
    SEMANTICSCHOLAR_RECOMMENDATIONS_BASE_URL,
)
from .filters import PaperSearchFilters
from .models import (
    Author,
    AutocompletePaper,
    Citation,
    CitationContext,
    DatasetDiff,
    DatasetDiffList,
    DatasetMetadata,
    DatasetSummary,
    Embedding,
    ExternalIds,
    Journal,
    OpenAccessPdf,
    Paper,
    PaperMatch,
    Patent,
    PatentCitations,
    PublicationVenue,
    Reference,
    RefMention,
    Release,
    S2FieldOfStudy,
    Sentence,
    Snippet,
    SnippetAnnotations,
    SnippetMatch,
    SnippetPaper,
    SnippetSearchResult,
    Tldr,
)
from .unwrapper import ScholiastUnwrapper

__all__ = [
    "__version__",
    "APIError",
    "AuthError",
    "AUTHOR_BATCH_MAX_IDS",
    "Author",
    "AuthorsClient",
    "AuthorsSyncClient",
    "AutocompletePaper",
    "BibliofabricError",
    "BULK_SEARCH_MAX_LIMIT",
    "Citation",
    "CitationContext",
    "ConfigurationError",
    "DatasetDiff",
    "DatasetDiffList",
    "DatasetMetadata",
    "DatasetSummary",
    "DatasetsClient",
    "DatasetsSyncClient",
    "Embedding",
    "ExternalIds",
    "Journal",
    "NetworkError",
    "NotFoundError",
    "OpenAccessPdf",
    "PAPER_BATCH_MAX_IDS",
    "PAPER_SEARCH_MAX_LIMIT",
    "Page",
    "Paper",
    "PaperMatch",
    "PaperSearchFilters",
    "PapersClient",
    "PapersSyncClient",
    "Patent",
    "PatentCitations",
    "PatentsClient",
    "PatentsSyncClient",
    "PublicationVenue",
    "RateLimitError",
    "RefMention",
    "Reference",
    "Release",
    "SEARCH_MAX_OFFSET",
    "SEMANTICSCHOLAR_DATASETS_BASE_URL",
    "SEMANTICSCHOLAR_DIALECT",
    "SEMANTICSCHOLAR_GRAPH_BASE_URL",
    "SEMANTICSCHOLAR_RECOMMENDATIONS_BASE_URL",
    "S2FieldOfStudy",
    "Sentence",
    "Snippet",
    "SnippetAnnotations",
    "SnippetMatch",
    "SnippetPaper",
    "SnippetSearchResult",
    "SnippetsClient",
    "SnippetsSyncClient",
    "TimeoutError",
    "ScholiastClient",
    "ScholiastResourceClient",
    "ScholiastResourceSyncClient",
    "ScholiastSettings",
    "ScholiastSyncClient",
    "ScholiastUnwrapper",
    "Tldr",
    "ValidationError",
    "get_settings",
]
