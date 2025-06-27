# aireloom/models/research_product.py
"""Pydantic models for representing OpenAIRE Research Product entities.

This module defines the Pydantic model for an OpenAIRE Research Product,
which can be a publication, dataset, software, or other research output.
It includes various nested models to represent complex fields like authors,
persistent identifiers (PIDs), access rights, citation impacts, instances, etc.,
based on the OpenAIRE data model documentation.
Reference: https://graph.openaire.eu/docs/data-model/entities/research-product
"""
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
"""Type alias for allowed Open Access routes (e.g., gold, green)."""

RefereedType = Literal["peerReviewed", "nonPeerReviewed", "UNKNOWN"]
"""Type alias for refereed status (e.g., peerReviewed, nonPeerReviewed)."""

ResearchProductType = Literal["publication", "dataset", "software", "other"]
"""Type alias for the type of research product (e.g., publication, dataset)."""

logger = logging.getLogger(__name__)


# Sub-models for nested structures


class Pid(BaseModel):
    """Represents a Persistent Identifier (PID) with its scheme and value.

    Attributes:
        scheme: The scheme of the PID (e.g., "doi", "orcid", "handle").
        value: The actual value of the PID.
    """
    scheme: str | None = None
    value: str | None = None

    model_config = ConfigDict(extra="allow")


class Author(BaseModel):
    """Represents an author of a research product.

    Attributes:
        fullName: The full name of the author.
        rank: The rank or order of the author in an author list.
        name: The given name(s) of the author.
        surname: The surname or family name of the author.
        pid: A `Pid` object representing a persistent identifier for the author (e.g., ORCID).
    """
    fullName: str | None = None
    rank: int | None = None
    name: str | None = None
    surname: str | None = None
    pid: Pid | None = None

    model_config = ConfigDict(extra="allow")


class BestAccessRight(BaseModel):
    """Represents the best determined access right for a research product.

    Attributes:
        code: The code representing the access right (e.g., "OPEN").
        label: A human-readable label for the access right (e.g., "Open Access").
        scheme: The scheme or vocabulary defining the access right code.
    """
    code: str | None = None
    label: str | None = None
    scheme: str | None = None

    model_config = ConfigDict(extra="allow")


class ResultCountry(BaseModel):
    """Represents the country associated with a research product or entity.

    Attributes:
        code: The ISO 3166-1 alpha-2 country code.
        label: The human-readable name of the country.
    """
    code: str | None = None
    label: str | None = None

    model_config = ConfigDict(extra="allow")


class CitationImpact(BaseModel):
    """Captures various citation-based impact metrics for a research product.

    Attributes:
        influence: A numerical score representing influence (meaning may vary).
        influenceClass: A categorical classification of influence (e.g., C1-C5).
        citationCount: The total number of citations received.
        citationClass: A categorical classification based on citation count.
        popularity: A numerical score representing popularity.
        popularityClass: A categorical classification of popularity.
        impulse: A numerical score representing research impulse or momentum.
        impulseClass: A categorical classification of impulse.
    """
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
    """Represents usage counts for a research product, like downloads and views.

    Includes a validator to coerce string values from the API into integers.

    Attributes:
        downloads: The number of times the research product has been downloaded.
        views: The number of times the research product has been viewed.
    """
    downloads: int | None = None
    views: int | None = None

    @field_validator("downloads", "views", mode="before")
    @classmethod
    def coerce_str_to_int(cls, v: Any) -> int | None:
        """Coerces string count values to integers, also handling None and logging errors.

        Args:
            v: The value to coerce.

        Returns:
            The value as an integer, or None if coercion is not possible or input is None.
        """
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
    """Container for various impact indicators of a research product.

    Attributes:
        citationImpact: A `CitationImpact` object detailing citation metrics.
        usageCounts: A `UsageCounts` object detailing view and download counts.
    """
    citationImpact: CitationImpact | None = None
    usageCounts: UsageCounts | None = None

    model_config = ConfigDict(extra="allow")


class AccessRight(BaseModel):
    """Represents the access rights associated with an instance of a research product.

    Attributes:
        code: A code representing the access right (e.g., "OPEN", "RESTRICTED").
        label: A human-readable label for the access right.
        openAccessRoute: The Open Access route, if applicable (e.g., "gold", "green").
        scheme: The scheme defining the access right codes.
    """
    code: str | None = None
    label: str | None = None
    openAccessRoute: OpenAccessRouteType | None = None
    scheme: str | None = None

    model_config = ConfigDict(extra="allow")


class ArticleProcessingCharge(BaseModel):
    """Represents Article Processing Charge (APC) information.

    Attributes:
        amount: The amount of the APC, typically as a string to accommodate various formats.
        currency: The currency code for the APC amount (e.g., "EUR", "USD").
    """
    amount: str | None = None
    currency: str | None = None

    model_config = ConfigDict(extra="allow")


class ResultPid(BaseModel): 
    """Represents a Persistent Identifier (PID) within a result context.

    Note: This model appears functionally identical to the top-level `Pid` model.
    Consider aliasing or reusing `Pid` if their semantics are indeed the same.

    Attributes:
        scheme: The scheme of the PID.
        value: The value of the PID.
    """
    scheme: str | None = None
    value: str | None = None

    model_config = ConfigDict(extra="allow")


class License(BaseModel): 
    """Represents license information.

    Note: This model was marked as potentially unused in the original API response
    analysis. It's kept for completeness but might not be populated.
    The `Instance.license` field is currently a simple string.

    Attributes:
        code: A code for the license (e.g., "CC-BY-4.0").
        label: A human-readable label for the license.
    """

    code: str | None = None
    label: str | None = None

    model_config = ConfigDict(extra="allow")


class Instance(BaseModel):
    """Represents a specific instance or manifestation of a research product.

    A research product can have multiple instances, for example, a preprint version,
    a published version in a journal, a copy in a repository, etc. Each instance
    can have its own access rights, license, and location.

    Attributes:
        accessRight: An `AccessRight` object detailing the access conditions for this instance.
        alternateIdentifier: A list of alternative identifiers for this instance.
        articleProcessingCharge: An `ArticleProcessingCharge` object, if applicable.
        license: A string representing the license of this instance.
                 (Note: API sometimes provides this as a simple string).
        collectedFrom: Information about the data source from which this instance was collected.
        hostedBy: Information about the data source hosting this instance.
        distributionLocation: The primary URL or location where this instance can be accessed.
        embargoEndDate: The date when an embargo on this instance ends (YYYY-MM-DD string).
        instanceId: A unique identifier for this specific instance.
        publicationDate: The publication date of this specific instance (YYYY-MM-DD string).
        refereed: The refereed status of this instance (`RefereedType`).
        type: The type of this instance (e.g., "fulltext", "abstract").
        urls: A list of URLs associated with this instance.
    """
    accessRight: AccessRight | None = None
    alternateIdentifier: list[dict[str, str]] = Field(default_factory=list)
    articleProcessingCharge: ArticleProcessingCharge | None = None
    license: str | None = (
        None
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
    """Represents a language associated with a research product.

    Attributes:
        code: The language code (e.g., "en", "fr").
        label: The human-readable name of the language (e.g., "English").
    """
    code: str | None = None
    label: str | None = None

    model_config = ConfigDict(extra="allow")


class Subject(BaseModel):
    """Represents a subject classification for a research product.

    The API often returns this as a nested dictionary where the key is the
    scheme (e.g., "ddc", "mesh") and the value is the subject term or code.
    This model captures that structure directly.

    Attributes:
        subject: A dictionary where keys are subject schemes and values are subject terms/codes.
                 Example: `{"fos": "Field of Science", "mesh": "D000001"}`
    """
    subject: dict[str, str] | None = None

    model_config = ConfigDict(extra="allow")


# Container for Publication
class Container(BaseModel):
    """Represents the container of a publication (e.g., journal, book series).

    Attributes:
        edition: The edition of the container.
        iss: The issue number of the container.
        issnLinking: The linking ISSN for a serial publication.
        issnOnline: The ISSN for the online version of a serial.
        issnPrinted: The ISSN for the printed version of a serial.
        name: The name of the container (e.g., journal title).
        sp: Start page of the item within the container.
        ep: End page of the item within the container.
        vol: Volume number of the container.
    """
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
    """Represents geolocation information, typically for datasets.

    Attributes:
        box: A bounding box defining a geographical area, often as a string
             of coordinates (e.g., "minLon,minLat,maxLon,maxLat").
        place: A human-readable name for the geographical location.
    """
    box: str | None = None
    place: str | None = None

    model_config = ConfigDict(extra="allow")


# Update main ResearchProduct model
class ResearchProduct(BaseEntity):
    """Model representing an OpenAIRE Research Product entity.

    This is a central model in OpenAIRE, representing various outputs of research
    such as publications, datasets, software, or other types. It aggregates
    numerous metadata fields. Inherits `id` from `BaseEntity`.

    Attributes:
        originalIds: A list of original identifiers for the research product.
        pids: A list of `Pid` objects representing persistent identifiers.
        type: The `ResearchProductType` (e.g., "publication", "dataset").
        title: The main title of the research product.
        authors: A list of `Author` objects.
        bestAccessRight: A `BestAccessRight` object indicating the determined access status.
        country: A `ResultCountry` object indicating the country associated with the product.
        description: A textual description or abstract of the research product.
        publicationDate: The publication date of the research product (YYYY-MM-DD string).
        publisher: The name of the publisher.
        indicators: An `Indicator` object containing citation and usage metrics.
        instances: A list of `Instance` objects representing different manifestations
                   or versions of the research product.
        language: A `Language` object for the primary language of the product.
        subjects: A list of `Subject` objects.
        container: A `Container` object if the product is part of a larger collection
                   (e.g., a journal for an article).
        geoLocation: A `GeoLocation` object, typically for datasets.
        keywords: A list of keywords. A validator attempts to parse comma-separated strings.
        journal: An alias or alternative field for `container`, often used for journal details.
                 (Note: API might use 'container' or 'journal' field for similar info).
    """

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
        """Attempts to split a comma-separated string of keywords into a list.

        If the input `v` is a string, it's split by commas, and each part is stripped
        of whitespace. If `v` is None or not a string, it's returned as is (or None
        if the string was empty after stripping).

        Args:
            v: The value to parse, expected to be a string or None.

        Returns:
            A list of keyword strings, or None if input was None or empty.
        """
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
        """Populates the `title` field from `mainTitle` if `title` is not present.

        The OpenAIRE API sometimes uses `mainTitle` for the primary title. This
        validator ensures that the `title` field in the Pydantic model is populated
        using `mainTitle` if `title` itself is missing in the input data, effectively
        aliasing `mainTitle` to `title`.

        Args:
            data: The raw input data dictionary before validation.

        Returns:
            The (potentially modified) input data dictionary.
        """
        if isinstance(data, dict) and "mainTitle" in data:
            if "title" not in data or data["title"] is None: # Ensure we don't overwrite an existing title
                data["title"] = data.pop("mainTitle")
            else: # title exists, no need to pop mainTitle if it's just a duplicate
                data.pop("mainTitle", None)
        return data


# Define the specific response type for ResearchProduct results
ResearchProductResponse = ApiResponse[ResearchProduct]
"""Type alias for an API response containing a list of `ResearchProduct` entities."""
