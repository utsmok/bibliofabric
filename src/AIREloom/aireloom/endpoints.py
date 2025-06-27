"""Defines OpenAIRE API endpoint paths, filter models, and related configurations.

This module centralizes the definitions for various OpenAIRE API endpoints,
including their relative paths and Pydantic models for request filter parameters.
It also provides utility functions related to endpoint configurations, such as
retrieving valid sort fields for an endpoint.

The filter models ensure type safety and validation for parameters passed to
the API client's search and iteration methods.
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Base URLs
GRAPH_API_BASE_URL = "https://api.graph.openaire.eu/v1/"
SCHOLIX_API_BASE_URL = (
    "https://api-beta.scholexplorer.openaire.eu/v3/"  # Scholexplorer v3 (beta)
)

# --- Graph API Endpoint Paths ---
RESEARCH_PRODUCTS = "researchProducts"
ORGANIZATIONS = "organizations"
DATA_SOURCES = "dataSources"
PROJECTS = "projects"
SCHOLIX = "Links"  # Renamed for Scholexplorer

# --- Pydantic Models for Filter Parameters ---


class ResearchProductsFilters(BaseModel):
    """Filter model for Research Products API endpoint."""

    search: str | None = None
    mainTitle: str | None = None
    description: str | None = None
    id: str | None = None
    pid: str | None = None
    originalId: str | None = None
    type: Literal["publication", "dataset", "software", "other"] | None = None
    fromPublicationDate: date | None = None
    toPublicationDate: date | None = None
    subjects: list[str] | None = None
    countryCode: str | None = None
    authorFullName: str | None = None
    authorOrcid: str | None = None
    publisher: str | None = None
    bestOpenAccessRightLabel: str | None = None
    influenceClass: str | None = None
    impulseClass: str | None = None
    popularityClass: str | None = None
    citationCountClass: str | None = None
    instanceType: str | None = None
    sdg: list[str] | None = None
    fos: list[str] | None = None
    isPeerReviewed: bool | None = None
    isInDiamondJournal: bool | None = None
    isPubliclyFunded: bool | None = None
    isGreen: bool | None = None
    openAccessColor: str | None = None
    relOrganizationId: str | None = None
    relCommunityId: str | None = None
    relProjectId: str | None = None
    relProjectCode: str | None = None
    hasProjectRel: bool | None = None
    relProjectFundingShortName: str | None = None
    relProjectFundingStreamId: str | None = None
    relHostingDataSourceId: str | None = None
    relCollectedFromDatasourceId: str | None = None

    model_config = ConfigDict(extra="forbid")


class OrganizationsFilters(BaseModel):
    """Filter model for Organizations API endpoint."""

    search: str | None = None
    legalName: str | None = None
    legalShortName: str | None = None
    id: str | None = None
    pid: str | None = None
    countryCode: str | None = None
    relCommunityId: str | None = None
    relCollectedFromDatasourceId: str | None = None

    model_config = ConfigDict(extra="forbid")


class DataSourcesFilters(BaseModel):
    """Filter model for Data Sources API endpoint."""

    search: str | None = None
    officialName: str | None = None
    englishName: str | None = None
    legalShortName: str | None = None
    id: str | None = None
    pid: str | None = None
    subjects: list[str] | None = None
    dataSourceTypeName: str | None = None
    contentTypes: list[str] | None = None
    openaireCompatibility: str | None = None  # Added based on test match_params
    relOrganizationId: str | None = None
    relCommunityId: str | None = None
    relCollectedFromDatasourceId: str | None = None

    model_config = ConfigDict(extra="forbid")


class ProjectsFilters(BaseModel):
    """Filter model for Projects API endpoint."""

    search: str | None = None
    title: str | None = None
    keywords: list[str] | None = None
    id: str | None = None
    code: str | None = None
    grantID: str | None = None  # Added based on test match_params
    acronym: str | None = None
    callIdentifier: str | None = None
    fundingStreamId: str | None = None
    fromStartDate: date | None = None
    toStartDate: date | None = None
    fromEndDate: date | None = None
    toEndDate: date | None = None
    relOrganizationName: str | None = None
    relOrganizationId: str | None = None
    relCommunityId: str | None = None
    relOrganizationCountryCode: str | None = None
    relCollectedFromDatasourceId: str | None = None

    model_config = ConfigDict(extra="forbid")


class ScholixFilters(BaseModel):
    sourcePid: str | None = None
    targetPid: str | None = None
    sourcePublisher: str | None = None
    targetPublisher: str | None = None
    sourceType: Literal["Publication", "Dataset", "Software", "Other"] | None = None
    targetType: Literal["Publication", "Dataset", "Software", "Other"] | None = None
    relation: str | None = None
    from_date: date | None = Field(default=None, alias="from")  # API uses "from"
    to_date: date | None = Field(default=None, alias="to")  # API uses "to"

    model_config = {"extra": "forbid", "populate_by_name": True}


# Basic definition structure: {path: {'filters_model': PydanticModel, 'sort': dict()}}
ENDPOINT_DEFINITIONS = {
    RESEARCH_PRODUCTS: {
        "filters_model": ResearchProductsFilters,
        "sort": {
            "relevance": {},
            "publicationDate": {},
            "dateOfCollection": {},
            "influence": {},
            "popularity": {},
            "citationCount": {},
            "impulse": {},
        },
    },
    ORGANIZATIONS: {
        "filters_model": OrganizationsFilters,
        "sort": {"relevance": {}, "legalname": {}, "id": {}},
    },
    DATA_SOURCES: {
        "filters_model": DataSourcesFilters,
        "sort": {"relevance": {}, "officialName": {}, "id": {}},
    },
    PROJECTS: {
        "filters_model": ProjectsFilters,
        "sort": {
            "relevance": {},
            "startDate": {},
            "endDate": {},
            "title": {},
            "acronym": {},
        },
    },
    SCHOLIX: {
        "filters_model": ScholixFilters,
        "sort": {},  # Sorting not specified for /Links endpoint
    },
}


def get_valid_sort_fields(endpoint_path: str) -> set[str]:
    """Returns the set of valid sort fields for a given endpoint path."""
    definitions = ENDPOINT_DEFINITIONS.get(endpoint_path, {})
    sort_definitions = definitions.get("sort", {})
    return set(sort_definitions.keys())
