# https://graph.openaire.eu/docs/data-model/entities/research-product

import logging
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from .base import ApiResponse, BaseEntity

"""
This module contains the Pydantic models for parsing & validation OpenAIRE API responses.
The models are designed to be used with the OpenAIRE Graph API and are structured to match
the expected JSON response format for Research Products.
"""

OpenAccessRouteType = Literal["gold", "green", "hybrid", "bronze"]
RefereedType = Literal["peerReviewed", "nonPeerReviewed", "UNKNOWN"]
ResearchProductType = Literal["publication", "dataset", "software", "other"]

logger = logging.getLogger(__name__)


# Sub-models for nested structures


class Pid(BaseModel):
    scheme: str | None = None
    value: str | None = None

    model_config = ConfigDict(extra="allow")


class Author(BaseModel):
    fullName: str | None = None
    rank: int | None = None
    name: str | None = None
    surname: str | None = None
    pid: Pid | None = None

    model_config = ConfigDict(extra="allow")


class BestAccessRight(BaseModel):
    code: str | None = None
    label: str | None = None
    scheme: str | None = None

    model_config = ConfigDict(extra="allow")


class ResultCountry(BaseModel):
    code: str | None = None
    label: str | None = None

    model_config = ConfigDict(extra="allow")


class CitationImpact(BaseModel):
    influence: float | None = None
    influenceClass: Literal["C1", "C2", "C3", "C4", "C5"] | None = None
    citationCount: int | None = None
    citationClass: Literal["C1", "C2", "C3", "C4", "C5"] | None = None
    popularity: float | None = None
    popularityClass: Literal["C1", "C2", "C3", "C4", "C5"] | None = None
    impulse: float | None = None
    impulseClass: Literal["C1", "C2", "C3", "C4", "C5"] | None = None

    model_config = ConfigDict(extra="allow")


class UsageCounts(BaseModel):
    downloads: int | None = None
    views: int | None = None

    @field_validator("downloads", "views", mode="before")
    @classmethod
    def coerce_str_to_int(cls, v: Any) -> int | None:
        """Coerce string count values to integers, handling None and errors."""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return int(v)
            except (ValueError, TypeError):
                logger.warning(f"Could not coerce UsageCounts value '{v}' to int.")
                return None
        if isinstance(v, int):
            return v
        logger.warning(f"Unexpected type {type(v)} for UsageCounts value '{v}'.")
        return None

    model_config = ConfigDict(extra="allow")


class Indicator(BaseModel):
    citationImpact: CitationImpact | None = None
    usageCounts: UsageCounts | None = None

    model_config = ConfigDict(extra="allow")


class AccessRight(BaseModel):
    code: str | None = None
    label: str | None = None
    openAccessRoute: OpenAccessRouteType | None = None
    scheme: str | None = None

    model_config = ConfigDict(extra="allow")


class ArticleProcessingCharge(BaseModel):
    amount: str | None = None
    currency: str | None = None

    model_config = ConfigDict(extra="allow")


class ResultPid(BaseModel):
    scheme: str | None = None
    value: str | None = None

    model_config = ConfigDict(extra="allow")


class License(BaseModel):
    """Unused?"""

    code: str | None = None
    label: str | None = None

    model_config = ConfigDict(extra="allow")


class Instance(BaseModel):
    accessRight: AccessRight | None = None
    alternateIdentifier: list[dict[str, str]] = Field(default_factory=list)
    articleProcessingCharge: ArticleProcessingCharge | None = None
    license: str | None = (
        None  # changed to str -- License objects seems to be unused in api?
    )
    collectedFrom: dict[str, str] | None = None
    hostedBy: dict[str, str] | None = None
    distributionLocation: str | None = None
    embargoEndDate: str | None = None
    instanceId: str | None = None
    publicationDate: str | None = None
    refereed: RefereedType | None = None
    type: str | None = None
    urls: list[str] = Field(default_factory=list)

    '''
    @field_validator("license", mode="before")
    @classmethod
    def handle_string_license(cls, v: Any) -> License | None:
        """Handle cases where license is provided as a simple string instead of an object."""
        if v is None:
            return None
        if isinstance(v, str):
            # If it's a string, create a License object with the string as both code and label
            return License(code=v, label=v)
        if isinstance(v, dict):
            return License(**v)
        if isinstance(v, License):
            return v
        logger.warning(
            f"Unexpected license format: {v}. Expected string, dict, or License object."
        )
        return None
    '''
    model_config = ConfigDict(extra="allow")


class Language(BaseModel):
    code: str | None = None
    label: str | None = None

    model_config = ConfigDict(extra="allow")


class Subject(BaseModel):
    subject: dict[str, str] | None = None

    model_config = ConfigDict(extra="allow")


# Container for Publication
class Container(BaseModel):
    edition: str | None = None
    iss: str | None = None
    issnLinking: str | None = None
    issnOnline: str | None = None
    issnPrinted: str | None = None
    name: str | None = None
    sp: str | None = None
    ep: str | None = None
    vol: str | None = None

    model_config = ConfigDict(extra="allow")


# GeoLocation for Data
class GeoLocation(BaseModel):
    box: str | None = None
    place: str | None = None

    model_config = ConfigDict(extra="allow")


# Update main ResearchProduct model
class ResearchProduct(BaseEntity):
    """Model representing an OpenAIRE Research Product entity."""

    # id is inherited from BaseEntity
    originalIds: list[str] | None = Field(default_factory=list)
    pids: list[Pid] | None = Field(default_factory=list)
    type: ResearchProductType | None = None
    title: str | None = None
    authors: list[Author] | None = Field(default_factory=list)
    bestAccessRight: BestAccessRight | None = None
    country: ResultCountry | None = None
    description: str | None = None
    publicationDate: str | None = None
    publisher: str | None = None
    indicators: Indicator | None = None
    instances: list[Instance] | None = Field(default_factory=list)
    language: Language | None = None
    subjects: list[Subject] | None = Field(default_factory=list)
    container: Container | None = None
    geoLocation: GeoLocation | None = None
    keywords: list[str] | None = Field(default_factory=list)
    journal: Container | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    @field_validator("keywords", mode="before")
    @classmethod
    def split_keywords(cls, v: Any) -> list[str] | None:
        """Split comma-separated keywords into a list."""
        if v is None:
            return None
        if isinstance(v, str):
            return [kw.strip() for kw in v.split(",") if kw.strip()]
        logger.warning(
            f"Unexpected value for ResearchProduct.keywords: {v}. Expected string or None."
        )
        return None  # Or raise ValueError if strictness is preferred

    @model_validator(mode="before")
    @classmethod
    def get_title_from_main_title(cls, data: Any) -> Any:
        """Populate title from mainTitle if title is not present."""
        if isinstance(data, dict) and "mainTitle" in data:
            data["title"] = data.pop("mainTitle")
        return data


# Define the specific response type for ResearchProduct results
ResearchProductResponse = ApiResponse[ResearchProduct]
