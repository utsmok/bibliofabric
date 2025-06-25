# https://graph.openaire.eu/docs/data-model/entities/project

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Import base classes
from .base import ApiResponse, BaseEntity


class FundingStream(BaseModel):
    """Details about the funding stream for a project."""

    description: str | None = None
    id: str | None = None
    model_config = ConfigDict(extra="allow")


class Funding(BaseModel):
    """Details about the funding source and stream."""

    fundingStream: FundingStream | None = None
    jurisdiction: str | None = None
    name: str | None = None
    shortName: str | None = None
    model_config = ConfigDict(extra="allow")


class Grant(BaseModel):
    """Details about the grant amounts."""

    currency: str | None = None
    fundedAmount: float | None = None
    totalCost: float | None = None
    model_config = ConfigDict(extra="allow")


class H2020Programme(BaseModel):
    """Details about the H2020 programme, if applicable."""

    code: str | None = None
    description: str | None = None
    model_config = ConfigDict(extra="allow")


class Project(BaseEntity):
    """Model representing an OpenAIRE Project entity."""

    # id is inherited from BaseEntity
    code: str | None = None
    acronym: str | None = None
    title: str | None = None
    callIdentifier: str | None = None
    fundings: list[Funding] | None = Field(default_factory=list)
    granted: Grant | None = None
    h2020Programmes: list[H2020Programme] | None = Field(default_factory=list)
    # Keywords might be a single string or a delimited string. Attempt parsing.
    keywords: list[str] | str | None = None
    openAccessMandateForDataset: bool | None = None
    openAccessMandateForPublications: bool | None = None
    # Dates are kept as string for safety due to potential missing parts or nulls.
    # Expected format is typically YYYY-MM-DD.
    startDate: str | None = None
    endDate: str | None = None
    subjects: list[str] | None = Field(default_factory=list)
    summary: str | None = None
    websiteUrl: str | None = None

    model_config = ConfigDict(extra="allow")

    @field_validator("keywords", mode="before")
    @classmethod
    def parse_keywords_string(cls, v: Any) -> list[str] | str | None:
        """Attempt to parse a keyword string into a list using common delimiters."""
        if isinstance(v, str):
            # Prioritize comma, then semicolon
            delimiters = [",", ";"]
            for delimiter in delimiters:
                parts = [part.strip() for part in v.split(delimiter) if part.strip()]
                if len(parts) > 1:
                    return parts
            # If no split produced multiple parts, return the original string (or None if it was empty)
            return v if v else None
        # If not a string (e.g., already a list or None), return as is
        return v


# Define the specific response type for projects
ProjectResponse = ApiResponse[Project]
