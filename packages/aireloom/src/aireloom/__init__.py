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

from ._async.client import AireloomClient
from ._async.resources import (
    DataSourcesResource,
    GraphResource,
    LinksResource,
    OrganizationsResource,
    PersonsResource,
    ProjectsResource,
    ResearchProductsResource,
    ScholixResource,
)
from ._sync.client import AireloomSyncClient
from ._sync.resources import (
    SyncDataSourcesResource,
    SyncGraphResource,
    SyncLinksResource,
    SyncOrganizationsResource,
    SyncPersonsResource,
    SyncProjectsResource,
    SyncResearchProductsResource,
    SyncScholixResource,
)
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
    ScholixRelationshipType,
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
    "AireloomSyncClient",
    "BaseEntity",
    "BibliofabricError",
    "ConfigurationError",
    "DataSourcesFilters",
    "DataSource",
    "DataSourcesResource",
    "GraphResource",
    "LinksFilters",
    "LinksResource",
    "NetworkError",
    "NotFoundError",
    "Organization",
    "OrganizationsFilters",
    "OrganizationsResource",
    "Page",
    "Person",
    "PersonsFilters",
    "PersonsResource",
    "Project",
    "ProjectsFilters",
    "ProjectsResource",
    "RateLimitError",
    "RELATION_INVERSES",
    "Relation",
    "RelationInfo",
    "RelationName",
    "ResearchProduct",
    "ResearchProductsFilters",
    "ResearchProductsResource",
    "relation_inverse",
    "ScholixFilters",
    "ScholixLinkProvider",
    "ScholixPublisher",
    "ScholixRelationship",
    "ScholixRelationshipType",
    "ScholixResource",
    "SyncDataSourcesResource",
    "SyncGraphResource",
    "SyncLinksResource",
    "SyncOrganizationsResource",
    "SyncPersonsResource",
    "SyncProjectsResource",
    "SyncResearchProductsResource",
    "SyncScholixResource",
    "TimeoutError",
    "ValidationError",
    "__version__",
]
