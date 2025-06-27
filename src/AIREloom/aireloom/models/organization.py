# aireloom/models/organization.py
"""Pydantic models for representing OpenAIRE Organization entities.

This module defines the Pydantic model for an OpenAIRE Organization,
including nested models for country and persistent identifiers (PIDs),
based on the OpenAIRE data model documentation.
Reference: https://graph.openaire.eu/docs/data-model/entities/organization
"""

from pydantic import BaseModel, ConfigDict, Field

# Import base classes
from .base import ApiResponse, BaseEntity


class Country(BaseModel):
    """Represents the country associated with an organization.

    Attributes:
        code: The ISO 3166-1 alpha-2 country code (e.g., "GR", "US").
        label: The human-readable name of the country (e.g., "Greece").
    """

    code: str | None = None
    label: str | None = None

    model_config = ConfigDict(extra="allow")


class OrganizationPid(BaseModel):
    """Represents a persistent identifier (PID) for an organization.

    Attributes:
        scheme: The scheme of the PID (e.g., "ror", "grid", "isni").
        value: The value of the PID.
    """

    scheme: str | None = None
    value: str | None = None

    model_config = ConfigDict(extra="allow")


class Organization(BaseEntity):
    """Model representing an OpenAIRE Organization entity.

    Captures details about an organization, including its names, website,
    country, and various persistent identifiers. Inherits the `id` field
    from `BaseEntity`.

    Attributes:
        legalShortName: The official short name or acronym of the organization.
        legalName: The full official legal name of the organization.
        alternativeNames: A list of other known names for the organization.
        websiteUrl: The URL of the organization's official website.
        country: A `Country` object representing the organization's country.
        pids: A list of `OrganizationPid` objects representing various PIDs
              associated with the organization.
    """

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
"""Type alias for an API response containing a list of `Organization` entities."""
