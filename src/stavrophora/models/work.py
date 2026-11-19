"""Pydantic models for the Work entity and its nested types."""

from pydantic import AliasChoices, Field

from .base import (
    Assertion,
    ClinicalTrialNumber,
    ContentDomain,
    Contributor,
    CrossRefDate,
    EntityModel,
    Event,
    FunderRef,
    Institution,
    IssnType,
    JournalIssue,
    LicenseRef,
    Link,
    Reference,
    RelationObject,
    Resource,
    StandardsBody,
    UpdateTo,
)
from .safe_types import IdSafeStr, SafeInt, SafeList, SafeStr, SafeStrList


class Work(EntityModel):
    """A Crossref work record.

    Field names are snake_case with kebab-case aliases matching the live
    API keys (``DOI``, ``container-title``, ``is-referenced-by-count``,
    ...). The Crossref spec is incomplete — ``extra="allow"`` keeps any
    field the API returns but the model does not declare.
    """

    # Identity
    doi: SafeStr | None = Field(None, alias="DOI")
    url: str | None = Field(None, alias="URL")
    title: SafeList[str] = Field(default_factory=list)
    subtitle: SafeList[str] = Field(default_factory=list)
    original_title: SafeList[str] = Field(default_factory=list, alias="original-title")
    short_title: SafeList[str] = Field(default_factory=list, alias="short-title")
    container_title: SafeList[str] = Field(
        default_factory=list, alias="container-title"
    )
    short_container_title: SafeList[str] = Field(
        default_factory=list, alias="short-container-title"
    )
    description: SafeStr | None = None

    # People
    author: SafeList[Contributor] = Field(default_factory=list)
    editor: SafeList[Contributor] = Field(default_factory=list)
    translator: SafeList[Contributor] = Field(default_factory=list)
    chair: SafeList[Contributor] = Field(default_factory=list)

    # Dates
    issued: CrossRefDate | None = None
    published: CrossRefDate | None = None
    published_print: CrossRefDate | None = Field(None, alias="published-print")
    published_online: CrossRefDate | None = Field(None, alias="published-online")
    created: CrossRefDate | None = None
    deposited: CrossRefDate | None = None
    indexed: CrossRefDate | None = None
    approved: CrossRefDate | None = None
    posted: CrossRefDate | None = None
    accepted: CrossRefDate | None = None

    # Classification
    type: str | None = None
    subtype: str | None = None
    publisher: SafeStr | None = None
    publisher_location: SafeStr | None = Field(None, alias="publisher-location")
    language: SafeStr | None = None
    subject: SafeList[str] = Field(default_factory=list)

    # Citation metrics
    is_referenced_by_count: SafeInt = Field(0, alias="is-referenced-by-count")
    references_count: SafeInt = Field(
        0, validation_alias=AliasChoices("references-count", "reference-count")
    )
    #: relevance score, present on list items when a query or relevance sort is used
    score: float | None = None
    source: SafeStr | None = None

    # Bibliographic
    issn: SafeList[str] = Field(default_factory=list, alias="ISSN")
    isbn: SafeList[str] = Field(default_factory=list, alias="ISBN")
    issn_type: SafeList[IssnType] = Field(default_factory=list, alias="issn-type")
    isbn_type: SafeList[IssnType] = Field(default_factory=list, alias="isbn-type")
    page: SafeStr | None = None
    volume: SafeStr | None = None
    issue: SafeStr | None = None
    article_number: SafeStr | None = Field(None, alias="article-number")
    edition_number: SafeStr | None = Field(None, alias="edition-number")
    journal_issue: JournalIssue | None = Field(None, alias="journal-issue")

    # Content
    abstract: SafeStr | None = None
    license: SafeList[LicenseRef] = Field(default_factory=list)
    funder: SafeList[FunderRef] = Field(default_factory=list)
    reference: SafeList[Reference] = Field(default_factory=list)
    link: SafeList[Link] = Field(default_factory=list)
    alternative_id: SafeList[str] = Field(default_factory=list, alias="alternative-id")

    # Provenance / relations
    #: bare member id (``"297"``) or ``https://id.crossref.org/member/297`` URI
    member: IdSafeStr | None = None
    #: bare prefix (``"10.1038"``) or ``https://id.crossref.org/prefix/10.1038`` URI
    prefix: IdSafeStr | None = None
    resource: Resource | None = None
    content_domain: ContentDomain | None = Field(None, alias="content-domain")
    #: ``{relation-type: [{id, id-type, asserted-by}]}``; relation types are open-ended
    relation: dict[str, SafeList[RelationObject]] | None = None
    update_policy: SafeStr | None = Field(None, alias="update-policy")
    update_to: SafeList[UpdateTo] = Field(default_factory=list, alias="update-to")
    group_title: SafeStr | None = Field(None, alias="group-title")
    clinical_trial_number: SafeList[ClinicalTrialNumber] = Field(
        default_factory=list, alias="clinical-trial-number"
    )
    #: Live API returns bare archive names (``["CLOCKSS", "LOCKSS", "Portico"]``).
    archive: SafeStrList = Field(default_factory=list)
    assertion: SafeList[Assertion] = Field(default_factory=list)
    event: Event | None = None
    agent: SafeStr | None = None
    institution: SafeList[Institution] = Field(default_factory=list)
    standards_body: StandardsBody | None = Field(None, alias="standards-body")
    #: documented in the swagger spec, not yet seen on live probes
    review: dict | None = None

    @property
    def primary_title(self) -> str:
        """First title string, or ``""`` when absent (SafeStr-style access)."""
        return self.title[0] if self.title else ""
