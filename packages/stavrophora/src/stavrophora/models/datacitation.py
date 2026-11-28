"""Pydantic models for the Crossref Data Citations API (beta)."""

from pydantic import Field

from .base import EntityModel
from .safe_types import SafeStr


class DataCitationEnd(EntityModel):
    """One end of a data citation: the citing work or the cited object.

    ``member`` is set on the subject only: the Crossref member that
    registered the citing work.
    """

    id: SafeStr | None = None
    type: SafeStr | None = None
    registration_agency: SafeStr | None = Field(None, alias="registration-agency")
    member: SafeStr | None = None


class DataCitation(EntityModel):
    """One data citation relationship from ``/beta/datacitations``.

    ``subject`` cites ``object`` with the relation type ``relation``
    (for example ``references``). ``timestamp`` is the ISO 8601 time at which
    Crossref added the relationship to its database.
    """

    timestamp: SafeStr | None = None
    relation: SafeStr | None = None
    subject: DataCitationEnd | None = None
    object: DataCitationEnd | None = None


__all__ = ["DataCitation", "DataCitationEnd"]
