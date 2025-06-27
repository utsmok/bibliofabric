# aireloom/models/project.py
"""Pydantic models for representing OpenAIRE Project entities and related structures.

This module defines the Pydantic model for an OpenAIRE Project,
including nested models for funding details, grants, and H2020 programme information,
based on the OpenAIRE data model documentation.
Reference: https://graph.openaire.eu/docs/data-model/entities/project
"""
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Import base classes
from .base import ApiResponse, BaseEntity


class FundingStream(BaseModel):
    """Represents details about a specific funding stream for a project.

    Attributes:
        description: A description of the funding stream.
        id: The unique identifier of the funding stream.
    """

    description: str | None = None
    id: str | None = None
    model_config = ConfigDict(extra="allow")


class Funding(BaseModel):
    """Represents funding information for a project, including the source and stream.

    Attributes:
        fundingStream: A `FundingStream` object detailing the specific stream.
        jurisdiction: The jurisdiction associated with the funding (e.g., country code).
        name: The name of the funding body or organization.
        shortName: An optional short name or acronym for the funding body.
    """

    fundingStream: FundingStream | None = None
    jurisdiction: str | None = None
    name: str | None = None
    shortName: str | None = None
    model_config = ConfigDict(extra="allow")


class Grant(BaseModel):
    """Represents details about the grant amounts associated with a project.

    Attributes:
        currency: The currency code for the amounts (e.g., "EUR", "USD").
        fundedAmount: The amount of funding awarded.
        totalCost: The total cost of the project.
    """

    currency: str | None = None
    fundedAmount: float | None = None
    totalCost: float | None = None
    model_config = ConfigDict(extra="allow")


class H2020Programme(BaseModel):
    """Represents details about an H2020 programme related to a project.

    Attributes:
        code: The code of the H2020 programme.
        description: A description of the H2020 programme.
    """

    code: str | None = None
    description: str | None = None
    model_config = ConfigDict(extra="allow")


class Project(BaseEntity):
    """Model representing an OpenAIRE Project entity.

    Captures comprehensive information about a research project, including its
    identifiers, title, funding, duration, and related metadata. Inherits the
    `id` field from `BaseEntity`.

    Attributes:
        code: The project code or grant number.
        acronym: The acronym of the project.
        title: The official title of the project.
        callIdentifier: Identifier for the funding call.
        fundings: A list of `Funding` objects detailing the project's funding sources.
        granted: A `Grant` object with information about the awarded grant amounts.
        h2020Programmes: A list of `H2020Programme` objects if the project is part of H2020.
        keywords: A list of keywords or a single string of keywords describing the project.
                  A validator attempts to parse comma or semicolon-separated strings.
        openAccessMandateForDataset: Boolean indicating if there's an open access
                                     mandate for datasets produced by the project.
        openAccessMandateForPublications: Boolean indicating if there's an open access
                                          mandate for publications from the project.
        startDate: The start date of the project (typically "YYYY-MM-DD" string).
        endDate: The end date of the project (typically "YYYY-MM-DD" string).
        subjects: A list of subject classifications for the project.
        summary: A summary or abstract of the project.
        websiteUrl: The URL of the project's official website.
    """

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
        """Attempts to parse a keyword string into a list of strings.

        If the input `v` is a string, this validator tries to split it by common
        delimiters (comma, then semicolon). If splitting results in more than one
        part, a list of stripped parts is returned. Otherwise, the original string
        (or None if empty) is returned. If `v` is not a string (e.g., already a
        list or None), it's returned as is.

        Args:
            v: The value to parse, expected to be a string, list, or None.

        Returns:
            A list of strings if parsing was successful and yielded multiple keywords,
            the original string if no parsing occurred or yielded a single part,
            or None if the input string was empty.
        """
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
"""Type alias for an API response containing a list of `Project` entities."""
