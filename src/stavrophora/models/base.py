"""Base Pydantic models for the Crossref API response envelope and shared nested types."""

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from .safe_types import SafeInt, SafeList, SafeStr


class EntityModel(BaseModel):
    """Shared base for Crossref entity and nested models.

    Every field is optional with a default so results requested with
    ``select`` (sparse fieldsets) still validate; ``extra="allow"`` keeps
    fields the API returns that the spec does not document.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Message[EntityType: BaseModel](BaseModel):
    """Body of a Crossref list response (the ``message`` envelope member)."""

    total_results: int | None = Field(None, alias="total-results")
    items_per_page: int | None = Field(None, alias="items-per-page")
    next_cursor: str | None = Field(None, alias="next-cursor")
    query: dict | None = None
    facets: dict | None = None
    items: list[EntityType] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class ApiResponse[EntityType: BaseModel](BaseModel):
    """Generic envelope for all Crossref responses.

    Every Crossref response is ``{status, message-type, message-version,
    message}``; list responses carry ``Message``-shaped ``message`` bodies.
    """

    status: str | None = None
    message_type: str | None = Field(None, alias="message-type")
    message_version: str | None = Field(None, alias="message-version")
    message: Message[EntityType] = Field(default_factory=Message)

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class CrossRefDate(EntityModel):
    """Crossref date object (``issued``, ``published``, ``created``, ...).

    Shape: ``{"date-parts": [[2021, 6, 11]], "timestamp": ..., "source": ...}``
    """

    date_parts: SafeList[SafeList[int]] = Field(
        default_factory=list, alias="date-parts"
    )
    date_time: str | None = Field(None, alias="date-time")
    timestamp: int | None = None
    source: str | None = None

    @property
    def year(self) -> int | None:
        """First year of the first date part, if present."""
        for part in self.date_parts:
            if part:
                return part[0]
        return None


class IssnType(EntityModel):
    """ISSN with its type (print/electronic)."""

    type: str | None = None
    value: str | None = None


class Counts(EntityModel):
    """DOI totals shared by journal and member records."""

    total_dois: SafeInt = Field(0, alias="total-dois")
    backfile_dois: SafeInt = Field(0, alias="backfile-dois")
    current_dois: SafeInt = Field(0, alias="current-dois")


class Breakdowns(EntityModel):
    """DOI counts by issued year (``[[year, count], ...]``)."""

    dois_by_issued_year: SafeList[tuple[int, int]] = Field(
        default_factory=list, alias="dois-by-issued-year"
    )


class Identifier(EntityModel):
    """External id ({``id``, ``id-type``, ``asserted-by``}) used for ROR ids,
    funder ids, and relation objects."""

    id: SafeStr | None = None
    id_type: SafeStr | None = Field(None, alias="id-type")
    asserted_by: SafeStr | None = Field(None, alias="asserted-by")


class ContributorRole(EntityModel):
    """Controlled-vocabulary role of a contributor (``{role, vocabulary}``)."""

    role: SafeStr | None = None
    vocabulary: SafeStr | None = None


class Affiliation(EntityModel):
    """Contributor affiliation (``{name, id: [...], place: [...]}``)."""

    name: SafeStr | None = None
    #: ROR etc. ids; the wire key is the singular ``id``
    ids: SafeList[Identifier] = Field(default_factory=list, alias="id")
    place: SafeList[str] = Field(default_factory=list)


class Contributor(EntityModel):
    """Author/editor/contributor/chair on a work."""

    given: str | None = None
    family: str | None = None
    name: str | None = None
    orcid: str | None = Field(None, validation_alias=AliasChoices("ORCID", "orcid"))
    affiliation: SafeList[Affiliation] = Field(default_factory=list)
    role: SafeList[ContributorRole] = Field(default_factory=list)
    sequence: str | None = None
    authenticated_orcid: bool | None = Field(None, alias="authenticated-orcid")
    suffix: str | None = None


class LicenseRef(EntityModel):
    """License entry on a work."""

    url: str | None = Field(None, alias="URL")
    content_version: str | None = Field(None, alias="content-version")
    delay_in_days: int | None = Field(None, alias="delay-in-days")
    start: CrossRefDate | None = None


class AwardInfo(EntityModel):
    """Award number grouping inside a funder entry."""

    award_number: SafeList[str] = Field(default_factory=list, alias="award-number")


class FunderRef(EntityModel):
    """Funder entry on a work (Funder Registry DOI + award numbers)."""

    name: str | None = None
    doi: str | None = Field(None, alias="DOI")
    award: SafeList[str] = Field(default_factory=list)
    award_info: SafeList[AwardInfo] = Field(default_factory=list, alias="award-info")
    id: SafeList[Identifier] = Field(default_factory=list)
    doi_asserted_by: str | None = Field(None, alias="doi-asserted-by")


class Reference(EntityModel):
    """Bibliographic reference on a work.

    Which keys are present varies by publisher; all are optional.
    """

    key: str | None = None
    doi: str | None = Field(None, alias="DOI")
    doi_asserted_by: str | None = Field(None, alias="doi-asserted-by")
    identifier: str | None = None
    unstructured: str | None = None
    author: str | None = None
    year: str | None = None
    volume: str | None = None
    issue: str | None = None
    first_page: str | None = Field(None, alias="first-page")
    journal_title: str | None = Field(None, alias="journal-title")
    article_title: str | None = Field(None, alias="article-title")
    series_title: str | None = Field(None, alias="series-title")
    volume_title: str | None = Field(None, alias="volume-title")
    issn: str | None = Field(None, alias="ISSN")
    #: bare string in references ("print"), not an ``{type, value}`` object
    issn_type: str | None = Field(None, alias="issn-type")
    type: str | None = None


class Link(EntityModel):
    """Full-text link on a work."""

    url: str | None = Field(None, alias="URL")
    content_type: str | None = Field(None, alias="content-type")
    content_version: str | None = Field(None, alias="content-version")
    intended_application: str | None = Field(None, alias="intended-application")


class AssertionGroup(EntityModel):
    """Named grouping of assertions on a work."""

    name: str | None = None
    label: str | None = None


class Assertion(EntityModel):
    """Publisher assertion on a work (history, license info, ...)."""

    name: str | None = None
    value: str | None = None
    label: str | None = None
    order: int | None = None
    url: str | None = Field(None, alias="URL")
    group: AssertionGroup | None = None


class ClinicalTrialNumber(EntityModel):
    """Clinical trial registration attached to a work."""

    clinical_trial_number: str | None = Field(None, alias="clinical-trial-number")
    registry: str | None = None


class Institution(EntityModel):
    """Institution associated with a work (e.g. posted-content affiliations)."""

    name: str | None = None
    acronym: SafeList[str] = Field(default_factory=list)
    place: SafeList[str] = Field(default_factory=list)
    department: SafeList[str] = Field(default_factory=list)


class StandardsBody(EntityModel):
    """Standards body of a standard work (``{name, acronym}``)."""

    name: str | None = None
    acronym: str | None = None


class Event(EntityModel):
    """Event (conference) associated with a proceedings work."""

    name: str | None = None
    acronym: str | None = None
    number: str | None = None
    location: str | None = None
    sponsor: str | None = None
    start: CrossRefDate | None = None
    end: CrossRefDate | None = None


class RelationObject(EntityModel):
    """One end of a relation: ``{id, id-type, asserted-by}``."""

    id: str | None = None
    id_type: str | None = Field(None, alias="id-type")
    asserted_by: str | None = Field(None, alias="asserted-by")


class ResourceUrl(EntityModel):
    """URL entry inside a work ``resource``."""

    url: str | None = Field(None, alias="URL")


class Resource(EntityModel):
    """Landing-page resources of a work."""

    primary: ResourceUrl | None = None
    secondary: SafeList[ResourceUrl] = Field(default_factory=list)


class ContentDomain(EntityModel):
    """Crossmark content domain of a work."""

    domain: SafeList[str] = Field(default_factory=list)
    crossmark_restriction: bool | None = Field(None, alias="crossmark-restriction")


class JournalIssue(EntityModel):
    """Issue details nested on a work (``journal-issue``)."""

    issue: str | None = None
    volume: str | None = None
    published_print: CrossRefDate | None = Field(None, alias="published-print")
    published_online: CrossRefDate | None = Field(None, alias="published-online")


class UpdateTo(EntityModel):
    """Entry in a work's ``update-to`` list (earlier versions)."""

    doi: str | None = Field(None, alias="DOI")
    type: str | None = None
    label: str | None = None
    source: str | None = None
    updated: CrossRefDate | None = None


__all__ = [
    "Affiliation",
    "ApiResponse",
    "Assertion",
    "AssertionGroup",
    "AwardInfo",
    "Breakdowns",
    "ClinicalTrialNumber",
    "ContentDomain",
    "Contributor",
    "ContributorRole",
    "Counts",
    "CrossRefDate",
    "EntityModel",
    "Event",
    "FunderRef",
    "Identifier",
    "Institution",
    "IssnType",
    "JournalIssue",
    "LicenseRef",
    "Link",
    "Message",
    "Reference",
    "RelationObject",
    "Resource",
    "ResourceUrl",
    "StandardsBody",
    "UpdateTo",
]
