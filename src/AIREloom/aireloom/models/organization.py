# https://graph.openaire.eu/docs/data-model/entities/organization

from pydantic import BaseModel, ConfigDict, Field

# Import base classes
from .base import ApiResponse, BaseEntity


class Country(BaseModel):
    """Represents the country associated with an organization."""

    code: str | None = None
    label: str | None = None

    model_config = ConfigDict(extra="allow")


class OrganizationPid(BaseModel):
    """Represents a persistent identifier for an organization."""

    scheme: str | None = None
    value: str | None = None

    model_config = ConfigDict(extra="allow")


class Organization(BaseEntity):
    """Model representing an OpenAIRE Organization entity."""

    # id is inherited from BaseEntity
    legalShortName: str | None = None
    legalName: str | None = None
    alternativeNames: list[str] | None = Field(default_factory=list)
    websiteUrl: str | None = None
    country: Country | None = None
    pids: list[OrganizationPid] | None = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


# Define the specific response type for organizations
OrganizationResponse = ApiResponse[Organization]
