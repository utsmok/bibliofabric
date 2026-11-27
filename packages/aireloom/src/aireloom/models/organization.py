# aireloom/models/organization.py
"""Pydantic models for representing OpenAIRE Organization entities.

Reference: https://graph.openaire.eu/docs/data-model/entities/organization
"""

from bibliofabric import SafeList, SafeStr
from pydantic import Field, computed_field

from .._helpers import extract_pid_by_scheme
from .base import (
    BaseEntity,
    CodeLabel,
    FundingHierarchy,
    Pid,
    SafeCfHbKeyValue,
    SafeCodeLabel,
)
from .research_product import RelatedRecord

Country = CodeLabel
"""Alias keeping the historical export name; organizations carry ``{code, label}``."""

SafeCountry = SafeCodeLabel


class Organization(BaseEntity):
    """Model representing an OpenAIRE Organization entity.

    Captures names, website, country, persistent identifiers, funding records,
    provenance, and related entity links. Inherits the ``id`` field from
    ``BaseEntity``.
    """

    legalShortName: SafeStr = ""
    legalName: SafeStr = ""
    alternativeNames: SafeList[str] = Field(default_factory=list)
    websiteUrl: str | None = None
    country: SafeCountry = Field(default_factory=Country)
    pids: SafeList[Pid] = Field(default_factory=list)
    originalIds: SafeList[str] = Field(default_factory=list)
    collectedFrom: SafeList[SafeCfHbKeyValue] = Field(default_factory=list)
    fundings: SafeList[FundingHierarchy] = Field(default_factory=list)
    links: SafeList[RelatedRecord] = Field(default_factory=list)

    @computed_field
    @property
    def ror_id(self) -> str | None:
        return extract_pid_by_scheme(self.pids, "ror")

    @computed_field
    @property
    def country_code(self) -> str | None:
        return (
            self.country.code
            if self.country.code and self.country.code != "UNKNOWN"
            else None
        )

    def __str__(self) -> str:
        parts = []
        if self.legalName:
            parts.append(self.legalName)
        if self.country_code:
            parts.append(f"({self.country_code})")
        if self.ror_id:
            parts.append(f"ROR:{self.ror_id}")
        return " | ".join(parts) if parts else f"Organization(id={self.id!r})"
