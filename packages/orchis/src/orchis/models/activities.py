"""Models for the ORCID activities sections.

Every activity element carries ``put-code``, ``source``, ``visibility`` and a
``path``. The section responses wrap their elements in group objects:
affiliation-style sections use ``affiliation-group[].summaries[]``, works and
peer reviews use ``group[].work-summary[]`` / ``peer-review-summary[]``.
"""

from bibliofabric import SafeList, SafeStr
from pydantic import BaseModel, ConfigDict, Field

from .common import (
    Amount,
    Citation,
    Contributors,
    ExternalIds,
    FuzzyDate,
    OrcidId,
    Organization,
    Source,
    TextValue,
    Title,
)
from .person import Person
from .values import IntValue


class _Element(BaseModel):
    """Fields every activity element carries."""

    created_date: IntValue | None = Field(default=None, alias="created-date")
    last_modified_date: IntValue | None = Field(
        default=None, alias="last-modified-date"
    )
    source: Source | None = None
    put_code: int | None = Field(default=None, alias="put-code")
    path: SafeStr | None = None
    visibility: SafeStr | None = None
    display_index: int | str | None = Field(default=None, alias="display-index")

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class _AffiliationElement(_Element):
    """Fields shared by the affiliation-style activity elements."""

    department_name: SafeStr | None = Field(default=None, alias="department-name")
    role_title: SafeStr | None = Field(default=None, alias="role-title")
    start_date: FuzzyDate | None = Field(default=None, alias="start-date")
    end_date: FuzzyDate | None = Field(default=None, alias="end-date")
    organization: Organization | None = None
    url: TextValue | None = None
    external_ids: ExternalIds | None = Field(default=None, alias="external-ids")

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class EducationSummary(_AffiliationElement):
    """One education entry (``role-title`` is the degree)."""


class EmploymentSummary(_AffiliationElement):
    """One employment entry."""


class QualificationSummary(_AffiliationElement):
    """One qualification entry ( memberships-like, often student status)."""


class MembershipSummary(_AffiliationElement):
    """One membership entry."""


class ServiceSummary(_AffiliationElement):
    """One service entry."""


class DistinctionSummary(_AffiliationElement):
    """One distinction or award entry."""


class InvitedPositionSummary(_AffiliationElement):
    """One invited position or honorary position entry."""


class _Group(BaseModel):
    """Fields every group carries."""

    last_modified_date: IntValue | None = Field(
        default=None, alias="last-modified-date"
    )

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class AffiliationGroup(_Group):
    """A group of affiliation summaries that ORCID considers the same claim."""

    summaries: SafeList[dict] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class _AffiliationSection(_Group):
    """Common shape of an affiliation-style section response."""

    affiliation_group: SafeList[AffiliationGroup] = Field(
        default_factory=list, alias="affiliation-group"
    )
    path: SafeStr | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    def put_codes(self) -> list[int]:
        """Return the put-codes of every summary in the section."""
        codes: list[int] = []
        for group in self.affiliation_group:
            for summary in group.summaries:
                for value in summary.values():
                    if isinstance(value, dict):
                        code = value.get("put-code")
                        if isinstance(code, int):
                            codes.append(code)
        return codes


class EducationsSection(_AffiliationSection):
    """The educations section."""


class EmploymentsSection(_AffiliationSection):
    """The employments section."""


class QualificationsSection(_AffiliationSection):
    """The qualifications section."""


class MembershipsSection(_AffiliationSection):
    """The memberships section."""


class ServicesSection(_AffiliationSection):
    """The services section."""


class DistinctionsSection(_AffiliationSection):
    """The distinctions section."""


class InvitedPositionsSection(_AffiliationSection):
    """The invited-positions section (invitation-to-peer-review is separate)."""


class WorkSummary(_Element):
    """One work summary as it appears in the works section."""

    title: Title | None = None
    journal_title: TextValue | None = Field(default=None, alias="journal-title")
    type: SafeStr | None = None
    publication_date: FuzzyDate | None = Field(default=None, alias="publication-date")
    external_ids: ExternalIds | None = Field(default=None, alias="external-ids")
    url: TextValue | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class WorkGroup(_Group):
    """A group of work summaries that ORCID considers the same work."""

    work_summary: SafeList[WorkSummary] = Field(
        default_factory=list, alias="work-summary"
    )

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class WorksSection(_Group):
    """The works section of the activities summary."""

    group: SafeList[WorkGroup] = Field(default_factory=list)
    path: SafeStr | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    def put_codes(self) -> list[int]:
        """Return the put-codes of every work summary in the section."""
        return [
            summary.put_code
            for group in self.group
            for summary in group.work_summary
            if summary.put_code is not None
        ]


class Work(_Element):
    """One full work, as answered by the single-item route."""

    title: Title | None = None
    journal_title: TextValue | None = Field(default=None, alias="journal-title")
    short_description: SafeStr | None = Field(default=None, alias="short-description")
    citation: Citation | None = None
    type: SafeStr | None = None
    publication_date: FuzzyDate | None = Field(default=None, alias="publication-date")
    external_ids: ExternalIds | None = Field(default=None, alias="external-ids")
    url: TextValue | None = None
    contributors: Contributors | None = None
    language_code: SafeStr | None = Field(default=None, alias="language-code")
    country: TextValue | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class FundingSummary(_Element):
    """One funding summary as it appears in the fundings section."""

    type: SafeStr | None = None
    title: Title | None = None
    organization: Organization | None = None
    external_ids: ExternalIds | None = Field(default=None, alias="external-ids")
    url: TextValue | None = None
    start_date: FuzzyDate | None = Field(default=None, alias="start-date")
    end_date: FuzzyDate | None = Field(default=None, alias="end-date")

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class FundingGroup(_Group):
    """A group of funding summaries that ORCID considers the same grant."""

    funding_summary: SafeList[FundingSummary] = Field(
        default_factory=list, alias="funding-summary"
    )

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class FundingsSection(_Group):
    """The fundings section of the activities summary."""

    group: SafeList[FundingGroup] = Field(default_factory=list)
    path: SafeStr | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    def put_codes(self) -> list[int]:
        """Return the put-codes of every funding summary in the section."""
        return [
            summary.put_code
            for group in self.group
            for summary in group.funding_summary
            if summary.put_code is not None
        ]


class Funding(_Element):
    """One full funding entry, as answered by the single-item route."""

    type: SafeStr | None = None
    organization_defined_type: TextValue | None = Field(
        default=None, alias="organization-defined-type"
    )
    title: Title | None = None
    short_description: SafeStr | None = Field(default=None, alias="short-description")
    amount: Amount | None = None
    url: TextValue | None = None
    start_date: FuzzyDate | None = Field(default=None, alias="start-date")
    end_date: FuzzyDate | None = Field(default=None, alias="end-date")
    external_ids: ExternalIds | None = Field(default=None, alias="external-ids")
    contributors: Contributors | None = None
    organization: Organization | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class PeerReviewSummary(_Element):
    """One peer review summary (fields modeled loosely; extra keys kept)."""

    review_group_id: SafeStr | None = Field(default=None, alias="review-group-id")
    review_url: TextValue | None = Field(default=None, alias="review-url")
    review_type: SafeStr | None = Field(default=None, alias="review-type")
    review_status: SafeStr | None = Field(default=None, alias="review-status")
    review_completion_date: FuzzyDate | None = Field(
        default=None, alias="review-completion-date"
    )

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class PeerReviewGroup(_Group):
    """A group of peer review summaries."""

    peer_review_summary: SafeList[PeerReviewSummary] = Field(
        default_factory=list, alias="peer-review-summary"
    )

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class PeerReviewsSection(_Group):
    """The peer-reviews section of the activities summary."""

    group: SafeList[PeerReviewGroup] = Field(default_factory=list)
    path: SafeStr | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    def put_codes(self) -> list[int]:
        """Return the put-codes of every peer review summary in the section."""
        return [
            summary.put_code
            for group in self.group
            for summary in group.peer_review_summary
            if summary.put_code is not None
        ]


class PeerReview(_Element):
    """One full peer review, as answered by the single-item route."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class ResearchResourceSummary(_Element):
    """One research resource summary (fields modeled loosely; extra keys kept)."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class ResearchResourcesSection(_Group):
    """The research-resources section of the activities summary."""

    path: SafeStr | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class ActivitiesSummary(BaseModel):
    """The activities summary with every section, empty or present.

    A section the record does not use is ``None``; the section route then
    answers 404 for the same record.
    """

    last_modified_date: IntValue | None = Field(
        default=None, alias="last-modified-date"
    )
    distinctions: DistinctionsSection | None = None
    educations: EducationsSection | None = None
    employments: EmploymentsSection | None = None
    fundings: FundingsSection | None = None
    invited_positions: InvitedPositionsSection | None = Field(
        default=None, alias="invited-positions"
    )
    memberships: MembershipsSection | None = None
    peer_reviews: PeerReviewsSection | None = Field(default=None, alias="peer-reviews")
    qualifications: QualificationsSection | None = None
    research_resources: ResearchResourcesSection | None = Field(
        default=None, alias="research-resources"
    )
    services: ServicesSection | None = None
    works: WorksSection | None = None
    path: SafeStr | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class History(BaseModel):
    """Record history: creation method, claimed flags, and timestamps."""

    creation_method: SafeStr | None = Field(default=None, alias="creation-method")
    completion_date: IntValue | None = Field(default=None, alias="completion-date")
    submission_date: IntValue | None = Field(default=None, alias="submission-date")
    last_modified_date: IntValue | None = Field(
        default=None, alias="last-modified-date"
    )
    claimed: bool | None = None
    verified_email: bool | None = Field(default=None, alias="verified-email")
    verified_phone: bool | None = Field(default=None, alias="verified-phone")
    source: Source | None = None
    visible: bool | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class OrchisRecord(BaseModel):
    """The full record summary (``/{orcid}/record``).

    Carries the person section and the activities summary alongside
    preferences and history.
    """

    orcid_identifier: OrcidId | None = Field(default=None, alias="orcid-identifier")
    preferences: dict | None = None
    history: History | None = None
    person: Person | None = None
    activities_summary: ActivitiesSummary | None = Field(
        default=None, alias="activities-summary"
    )
    path: SafeStr | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


__all__ = [
    "ActivitiesSummary",
    "DistinctionSummary",
    "DistinctionsSection",
    "EducationSummary",
    "EducationsSection",
    "EmploymentSummary",
    "EmploymentsSection",
    "Funding",
    "FundingGroup",
    "FundingSummary",
    "FundingsSection",
    "History",
    "InvitedPositionSummary",
    "InvitedPositionsSection",
    "MembershipSummary",
    "MembershipsSection",
    "PeerReview",
    "PeerReviewGroup",
    "PeerReviewSummary",
    "PeerReviewsSection",
    "QualificationSummary",
    "QualificationsSection",
    "ResearchResourceSummary",
    "ResearchResourcesSection",
    "ServiceSummary",
    "ServicesSection",
    "OrchisRecord",
    "Work",
    "WorkGroup",
    "WorkSummary",
    "WorksSection",
]
