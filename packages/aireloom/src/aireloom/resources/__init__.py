"""Resource clients for the OpenAIRE Graph and Scholexplorer APIs."""

from .base import GraphResource
from .data_sources import DataSourcesResource
from .links import LinksResource
from .organizations import OrganizationsResource
from .persons import PersonsResource
from .projects import ProjectsResource
from .research_products import ResearchProductsResource
from .scholix import ScholixResource

__all__ = [
    "DataSourcesResource",
    "GraphResource",
    "LinksResource",
    "OrganizationsResource",
    "PersonsResource",
    "ProjectsResource",
    "ResearchProductsResource",
    "ScholixResource",
]
