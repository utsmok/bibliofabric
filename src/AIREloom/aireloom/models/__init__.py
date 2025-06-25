"""Pydantic models for OpenAIRE API entities and responses."""

# Combined & Sorted Imports
from .base import ApiResponse, BaseEntity, Header
from .data_source import ControlledField, DataSource, DataSourceResponse
from .organization import Country, Organization, OrganizationPid, OrganizationResponse
from .project import (
    Funding,
    FundingStream,
    Grant,
    H2020Programme,
    Project,
    ProjectResponse,
)
from .research_product import ResearchProduct, ResearchProductResponse
from .scholix import (
    ScholixCreator,
    ScholixEntity,
    ScholixIdentifier,
    ScholixLinkProvider,
    ScholixPublisher,
    ScholixRelationship,
    ScholixResponse,
)

__all__ = [
    "ApiResponse",
    "BaseEntity",
    "ControlledField",
    "Country",
    "DataSource",
    "DataSourceResponse",
    "Funding",
    "FundingStream",
    "Grant",
    "H2020Programme",
    "Header",
    "Organization",
    "OrganizationPid",
    "OrganizationResponse",
    "Project",
    "ProjectResponse",
    "ResearchProduct",
    "ResearchProductResponse",
    "ScholixCreator",
    "ScholixEntity",
    # "ScholixEntityType", # Removed as per user request
    "ScholixIdentifier",
    "ScholixLinkProvider",
    "ScholixPublisher",
    "ScholixRelationship",
    "ScholixResponse",
]
