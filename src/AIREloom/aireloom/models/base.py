"""Base Pydantic models for OpenAIRE API entities and responses.

This module defines foundational Pydantic models used across the `aireloom`
library to represent common structures in OpenAIRE API responses, such as
response headers, base entity identifiers, and generic API response envelopes.
These models provide data validation and a clear structure for API data.
"""

import logging
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field, HttpUrl, field_validator  # Added Field
from pydantic.config import ConfigDict  # Added ConfigDict

# Generic type for the entity contained within the response results
EntityType = TypeVar("EntityType", bound="BaseEntity")
logger = logging.getLogger(__name__)


class Header(BaseModel):
    """Represents the 'header' section commonly found in OpenAIRE API responses.

    This model captures metadata about the API response, such as status,
    query time, total number of results found (`numFound`), pagination details
    like `nextCursor`, and page size. It includes validators to coerce
    numeric fields that might be returned as strings by the API.

    Attributes:
        status: Optional status message from the API.
        code: Optional status code from the API.
        message: Optional descriptive message from the API.
        queryTime: Time taken by the API to process the query, in milliseconds.
        numFound: Total number of results found matching the query criteria.
        nextCursor: The cursor string to use for fetching the next page of results.
                    Can be a string or an HttpUrl.
        pageSize: The number of results included in the current page.
    """

    # Note: status, code, message are typically expected, but optional for robustness.
    status: str | None = None
    code: str | None = None
    message: str | None = None
    # total and count are often strings in the API response, needs validation/coercion
    queryTime: int | None = None
    numFound: int | None = None  # next/prev can be full URLs or just the cursor string
    nextCursor: str | HttpUrl | None = Field(default=None)  # API returns "nextCursor"
    pageSize: int | None = None

    @field_validator("queryTime", "numFound", "pageSize", mode="before")
    @classmethod
    def coerce_str_to_int(cls, v: Any) -> int | None:
        """Coerce string representations of numbers to integers, logging on failure."""
        if isinstance(v, str):
            try:
                return int(v)
            except (ValueError, TypeError):
                logger.warning(f"Could not coerce header value '{v}' to int.")
                return None
        # Allow integers through if they somehow bypass 'before' validation or API changes
        if isinstance(v, int):
            return v
        # Handle other unexpected types if necessary
        logger.warning(f"Unexpected type {type(v)} for header numeric value '{v}'.")
        return None

    model_config = ConfigDict(extra="allow")


class BaseEntity(BaseModel):
    """A base Pydantic model for OpenAIRE entities (e.g., publication, project).

    This model provides a common foundation for all specific entity types,
    primarily by ensuring an `id` field is present, which is a common
    identifier across most OpenAIRE entities. It allows extra fields from the
    API to be captured without causing validation errors.

    Attributes:
        id: The unique identifier for the entity.
    """

    # Common identifier across most entities
    id: str

    model_config = ConfigDict(extra="allow")


class ApiResponse(BaseModel, Generic[EntityType]):
    """Generic Pydantic model for standard OpenAIRE API list responses.

    This model represents the common envelope structure for API responses that
    return a list of entities. It includes a `header` (metadata) and a `results`
    field containing the list of entities. It is generic over `EntityType` to
    allow specific entity types to be used in the `results` list.

    Attributes:
        header: A `Header` object containing metadata about the response.
        results: An optional list of entities of type `EntityType`. A validator
                 ensures this field is a list or None, handling potential API
                 inconsistencies gracefully.
    """

    header: Header
    # Results can sometimes be null/absent, sometimes an empty list
    results: list[EntityType] | None = None

    @field_validator("results", mode="before")
    @classmethod
    def handle_null_results(cls, v: Any) -> list[EntityType] | None:
        """Ensure 'results' is a list or None.

        Handles potential None or unexpected formats from the API.
        Logs a warning and returns an empty list for unexpected types.
        """
        if v is None:
            return None  # Explicitly return None if API sends null
        if isinstance(v, list):
            return v  # Already a list

        # Handle unexpected formats (e.g., dict wrappers like {'result': [...]})
        # or other non-list types by logging and returning an empty list.
        logger.warning(
            f"Unexpected format for 'results' field: {type(v)}. "
            f"Expected list or None, got {v!r}. Returning empty list."
        )
        return []

    model_config = ConfigDict(extra="allow")


# Example of a specific response type (for illustration)
# class ResearchProductResponse(ApiResponse[ResearchProduct]):
#     pass
