"""Pydantic models for Crossref journal, funder, member, type, prefix and license entities."""

from typing import Any

from pydantic import Field

from .base import Breakdowns, Counts, EntityModel, IssnType
from .safe_types import IdSafeStr, SafeInt, SafeList, SafeStr, SafeStrList


class MemberPrefix(EntityModel):
    """Prefix entry on a member record (``{name, value}``)."""

    name: SafeStr | None = None
    value: SafeStr | None = None


class Journal(EntityModel):
    """A Crossref journal (list item and ``/journals/{issn}`` record)."""

    #: bare string on ``/journals/{issn}``, list on ``/journals`` — SafeStrList handles both
    title: SafeStrList = Field(default_factory=list)
    publisher: SafeStr | None = None
    issn: SafeList[str] = Field(default_factory=list, alias="ISSN")
    issn_type: SafeList[IssnType] = Field(default_factory=list, alias="issn-type")
    counts: Counts | None = None
    #: ``{coverage-key: fraction}``; coverage keys are open-ended
    coverage: dict[str, float] | None = None
    #: nested per ``{all, backfile, current}``, each ``{coverage-key: fraction}``;
    #: coverage keys are open-ended
    coverage_type: dict[str, dict[str, float]] | None = Field(
        None, alias="coverage-type"
    )
    flags: dict[str, bool] | None = None
    breakdowns: Breakdowns | None = None
    subjects: SafeList[str] = Field(default_factory=list)
    last_status_check_time: float | None = Field(None, alias="last-status-check-time")

    @property
    def primary_title(self) -> str:
        """First title string, or ``""`` when absent."""
        return self.title[0] if self.title else ""


class Funder(EntityModel):
    """A Crossref funder (Funder Registry record).

    ``hierarchy`` fields only appear on ``/funders/{id}`` records, not
    on funder list items.
    """

    id: SafeStr | None = None
    name: SafeStr | None = None
    tokens: SafeList[str] = Field(default_factory=list)
    uri: SafeStr | None = None
    location: SafeStr | None = None
    alt_names: SafeList[str] = Field(default_factory=list, alias="alt-names")
    replaces: SafeList[str] = Field(default_factory=list)
    replaced_by: SafeList[str] = Field(default_factory=list, alias="replaced-by")
    work_count: SafeInt = Field(0, alias="work-count")
    descendant_work_count: SafeInt = Field(0, alias="descendant-work-count")
    #: nested ``{funder-id: {child-funder-id: {...}}}`` tree; recursive, so kept as dicts
    hierarchy: dict[str, Any] | None = None
    hierarchy_names: dict[str, str] | None = Field(None, alias="hierarchy-names")
    descendants: SafeList[str] = Field(default_factory=list)


class Member(EntityModel):
    """A Crossref member (publisher account)."""

    id: int | None = None
    primary_name: SafeStr | None = Field(None, alias="primary-name")
    names: SafeList[str] = Field(default_factory=list)
    prefixes: SafeList[str] = Field(default_factory=list)
    prefix: SafeList[MemberPrefix] = Field(default_factory=list)
    tokens: SafeList[str] = Field(default_factory=list)
    location: SafeStr | None = None
    counts: Counts | None = None
    counts_type: dict[str, dict[str, int]] | None = Field(None, alias="counts-type")
    coverage: dict[str, float] | None = None
    coverage_type: dict[str, dict[str, dict[str, float]]] | None = Field(
        None, alias="coverage-type"
    )
    flags: dict[str, bool] | None = None
    breakdowns: Breakdowns | None = None
    last_status_check_time: float | None = Field(None, alias="last-status-check-time")


class CrossRefType(EntityModel):
    """A Crossref work type (e.g. ``journal-article``)."""

    id: SafeStr | None = None
    label: SafeStr | None = None


class Prefix(EntityModel):
    """A Crossref DOI prefix owned by a member.

    ``/prefixes/{prefix}`` returns ``member``/``prefix`` as full
    ``https://id.crossref.org/...`` URIs (live 2026-09); ``IdSafeStr``
    normalizes both URI and bare forms to the bare value.
    """

    member: IdSafeStr | None = None
    name: SafeStr | None = None
    prefix: IdSafeStr | None = None


class License(EntityModel):
    """A Crossref license (list item on ``/licenses``)."""

    url: str | None = Field(None, alias="URL")
    work_count: int = Field(0, alias="work-count")
