# aireloom/resources/__init__.py
"""Exposes the resource client classes."""

from .base_client import BaseResourceClient
from .data_sources_client import DataSourcesClient
from .organizations_client import OrganizationsClient
from .projects_client import ProjectsClient
from .research_products_client import ResearchProductsClient
from .scholix_client import ScholixClient

__all__ = [
    "BaseResourceClient",
    "DataSourcesClient",
    "OrganizationsClient",
    "ProjectsClient",
    "ResearchProductsClient",
    "ScholixClient",
]
