"""Pydantic model for the DOI registration agency lookup."""

from pydantic import Field

from .base import EntityModel
from .safe_types import SafeStr


class Agency(EntityModel):
    """Registration agency for a DOI."""

    id: SafeStr | None = None
    label: SafeStr | None = None


class WorkAgency(EntityModel):
    """Response of ``GET /works/{doi}/agency``."""

    doi: SafeStr | None = Field(None, alias="DOI")
    agency: Agency | None = None
