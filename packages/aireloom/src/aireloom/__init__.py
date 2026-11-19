"""AIREloom: a Python client for the OpenAIRE Graph and Scholexplorer APIs."""

from importlib.metadata import PackageNotFoundError, version

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
from bibliofabric.paging import Page

from .client import AireloomClient
from .config import AireloomSettings
from .filters import (
    DataSourcesFilters,
    LinksFilters,
    OrganizationsFilters,
    PersonsFilters,
    ProjectsFilters,
    ResearchProductsFilters,
    ScholixFilters,
)
from .models import (
    BaseEntity,
    DataSource,
    Organization,
    Person,
    Project,
    Relation,
    RelationInfo,
    ResearchProduct,
    ScholixLinkProvider,
    ScholixPublisher,
    ScholixRelationship,
)
from .relations import (
    RELATION_INVERSES,
    RelationName,
    relation_inverse,
)

try:
    __version__: str = version("aireloom")
except PackageNotFoundError:  # pragma: no cover - package not installed
    __version__: str = "0.0.0"

__all__ = [
    "APIError",
    "AuthError",
    "AireloomClient",
    "AireloomSettings",
    "BaseEntity",
    "BibliofabricError",
    "ConfigurationError",
    "DataSourcesFilters",
    "DataSource",
    "LinksFilters",
    "NetworkError",
    "NotFoundError",
    "Organization",
    "OrganizationsFilters",
    "Page",
    "Person",
    "PersonsFilters",
    "Project",
    "ProjectsFilters",
    "RateLimitError",
    "RELATION_INVERSES",
    "Relation",
    "RelationInfo",
    "RelationName",
    "ResearchProduct",
    "ResearchProductsFilters",
    "relation_inverse",
    "ScholixFilters",
    "ScholixLinkProvider",
    "ScholixPublisher",
    "ScholixRelationship",
    "TimeoutError",
    "ValidationError",
    "__version__",
]
