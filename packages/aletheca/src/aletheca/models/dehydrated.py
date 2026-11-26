"""Pydantic models for dehydrated (partial) entity representations."""

from bibliofabric import SafeList, SafeStr
from pydantic import AliasChoices, BaseModel, Field
from pydantic.config import ConfigDict

from .base import BaseEntity


class DehydratedAuthor(BaseEntity):
    """Minimal author info embedded in authorships."""

    orcid: SafeStr | None = None
    observed_orcids: SafeList[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


class DehydratedInstitution(BaseEntity):
    """Minimal institution info embedded in other entities."""

    country_code: SafeStr | None = None
    ror: SafeStr | None = None
    type: str | None = None
    lineage: SafeList[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


class RelatedInstitution(DehydratedInstitution):
    """Dehydrated institution with relationship type."""

    relationship: str | None = None


class RelatedWork(BaseEntity):
    """Dehydrated work with its link type (an entry of ``Work.parent_works``).

    ``link_type`` is one of the part-of kinds OpenAlex defines:
    ``volume``, ``component``, ``data-series`` or ``part``. OpenAlex
    renamed the response field from ``relationship`` (the old name stops
    being served on 2026-12-07); validation accepts either, so payloads
    harvested before the cutover keep parsing.
    """

    link_type: SafeStr | None = Field(
        None, validation_alias=AliasChoices("link_type", "relationship")
    )

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class DehydratedInstitutionWithYear(BaseModel):
    """Institution with years of affiliation."""

    institution: DehydratedInstitution | None = None
    years: SafeList[int] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


class SimpleDehydratedConcept(BaseEntity):
    """Minimal concept info (deprecated entity)."""

    level: int | None = None
    wikidata: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class DehydratedConcept(SimpleDehydratedConcept):
    """Concept with relevance score (deprecated entity)."""

    score: float = 0.0

    model_config = ConfigDict(extra="allow")


class DehydratedSource(BaseEntity):
    """Minimal source info embedded in locations."""

    is_core: bool | None = None
    is_oa: bool | None = None
    is_in_doaj: bool | None = None
    issn: SafeList[str] = Field(default_factory=list)
    issn_l: SafeStr | None = None
    listed_in: SafeList[str] = Field(default_factory=list)
    type: str | None = None
    host_organization: SafeStr | None = None
    host_organization_name: SafeStr | None = None
    host_organization_lineage: SafeList[str] = Field(default_factory=list)
    host_organization_lineage_names: SafeList[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")
