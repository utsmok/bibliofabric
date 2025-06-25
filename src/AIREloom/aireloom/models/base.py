"""Base Pydantic models for API entities and responses."""

import logging
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field, HttpUrl, field_validator  # Added Field
from pydantic.config import ConfigDict  # Added ConfigDict

# Generic type for the entity contained within the response results
EntityType = TypeVar("EntityType", bound="BaseEntity")
logger = logging.getLogger(__name__)


class Header(BaseModel):
    """Model for the standard API response header."""

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
    """Base model for all OpenAIRE entities (like publication, project, etc.)."""

    # Common identifier across most entities
    id: str

    model_config = ConfigDict(extra="allow")


class ApiResponse(BaseModel, Generic[EntityType]):
    """Generic base model for standard API list responses."""

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
