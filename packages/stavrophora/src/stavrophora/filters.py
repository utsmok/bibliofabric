"""Pydantic filter models for the Crossref API.

Crossref filter syntax: ``filter=field:value,field:value`` — repeated keys
act as OR (``filter=doi:a,doi:b``), different keys as AND. The field lists
mirror the live API's advertised filters (verified 2026-11); unknown filters
are accepted through ``extra="allow"`` and serialized with their literal
name.
"""

from pydantic import BaseModel, ConfigDict, Field


class _CrossrefFilters(BaseModel):
    """Shared config: kebab-case wire names, unknown filters preserved."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class WorksFilters(_CrossrefFilters):
    """Filter model for the works routes (top-level and scoped)."""

    # Type / classification
    type: str | None = None
    type_name: str | None = Field(None, alias="type-name")
    category_name: str | None = Field(None, alias="category-name")
    group_title: str | None = Field(None, alias="group-title")
    directory: str | None = None

    # Identifiers
    doi: str | None = None
    issn: str | None = None
    isbn: str | None = None
    orcid: str | None = None
    ror_id: str | None = Field(None, alias="ror-id")
    prefix: str | None = None
    member: str | None = None
    container_title: str | None = Field(None, alias="container-title")
    alternative_id: str | None = Field(None, alias="alternative-id")
    article_number: str | None = Field(None, alias="article-number")
    archive: str | None = None
    content_domain: str | None = Field(None, alias="content-domain")
    project_id: str | None = Field(None, alias="project-id")

    # Publication dates (YYYY, YYYY-MM, or YYYY-MM-DD)
    from_pub_date: str | None = Field(None, alias="from-pub-date")
    until_pub_date: str | None = Field(None, alias="until-pub-date")
    from_print_pub_date: str | None = Field(None, alias="from-print-pub-date")
    until_print_pub_date: str | None = Field(None, alias="until-print-pub-date")
    from_online_pub_date: str | None = Field(None, alias="from-online-pub-date")
    until_online_pub_date: str | None = Field(None, alias="until-online-pub-date")
    from_issued_date: str | None = Field(None, alias="from-issued-date")
    until_issued_date: str | None = Field(None, alias="until-issued-date")
    from_accepted_date: str | None = Field(None, alias="from-accepted-date")
    until_accepted_date: str | None = Field(None, alias="until-accepted-date")
    from_approved_date: str | None = Field(None, alias="from-approved-date")
    until_approved_date: str | None = Field(None, alias="until-approved-date")
    from_awarded_date: str | None = Field(None, alias="from-awarded-date")
    until_awarded_date: str | None = Field(None, alias="until-awarded-date")
    from_posted_date: str | None = Field(None, alias="from-posted-date")
    until_posted_date: str | None = Field(None, alias="until-posted-date")
    from_event_start_date: str | None = Field(None, alias="from-event-start-date")
    until_event_start_date: str | None = Field(None, alias="until-event-start-date")
    from_event_end_date: str | None = Field(None, alias="from-event-end-date")
    until_event_end_date: str | None = Field(None, alias="until-event-end-date")

    # System dates — incremental sync (prefer created/deposit windows: cursor
    # result sets under index-date windows are not stable since 2026-08-24)
    from_index_date: str | None = Field(None, alias="from-index-date")
    until_index_date: str | None = Field(None, alias="until-index-date")
    from_created_date: str | None = Field(None, alias="from-created-date")
    until_created_date: str | None = Field(None, alias="until-created-date")
    from_deposit_date: str | None = Field(None, alias="from-deposit-date")
    until_deposit_date: str | None = Field(None, alias="until-deposit-date")
    from_update_date: str | None = Field(None, alias="from-update-date")
    until_update_date: str | None = Field(None, alias="until-update-date")

    # Updates
    update_type: str | None = Field(None, alias="update-type")
    updates: str | None = None
    is_update: bool | None = Field(None, alias="is-update")

    # Citation thresholds
    gte_citation: int | None = Field(None, alias="gte-citation")
    lte_citation: int | None = Field(None, alias="lte-citation")

    # Funding
    funder: str | None = None
    award_number: str | None = Field(None, alias="award.number")
    award_funder: str | None = Field(None, alias="award.funder")
    funder_doi_asserted_by: str | None = Field(None, alias="funder-doi-asserted-by")
    gte_award_amount: int | None = Field(None, alias="gte-award-amount")
    lte_award_amount: int | None = Field(None, alias="lte-award-amount")

    # Licenses / full text
    license_url: str | None = Field(None, alias="license.url")
    license_version: str | None = Field(None, alias="license.version")
    license_delay: str | None = Field(None, alias="license.delay")
    full_text_application: str | None = Field(None, alias="full-text.application")
    full_text_type: str | None = Field(None, alias="full-text.type")
    full_text_version: str | None = Field(None, alias="full-text.version")

    # Relations
    relation_object: str | None = Field(None, alias="relation.object")
    relation_object_type: str | None = Field(None, alias="relation.object-type")
    relation_type: str | None = Field(None, alias="relation.type")

    # Publisher assertions
    assertion: str | None = None
    assertion_group: str | None = Field(None, alias="assertion-group")
    clinical_trial_number: str | None = Field(None, alias="clinical-trial-number")

    # Boolean presence filters
    has_abstract: bool | None = Field(None, alias="has-abstract")
    has_affiliation: bool | None = Field(None, alias="has-affiliation")
    has_affiliation_ror_id: bool | None = Field(None, alias="has-affiliation-ror-id")
    has_authenticated_orcid: bool | None = Field(None, alias="has-authenticated-orcid")
    has_archive: bool | None = Field(None, alias="has-archive")
    has_assertion: bool | None = Field(None, alias="has-assertion")
    has_award: bool | None = Field(None, alias="has-award")
    has_clinical_trial_number: bool | None = Field(
        None, alias="has-clinical-trial-number"
    )
    has_content_domain: bool | None = Field(None, alias="has-content-domain")
    has_domain_restriction: bool | None = Field(None, alias="has-domain-restriction")
    has_event: bool | None = Field(None, alias="has-event")
    has_full_text: bool | None = Field(None, alias="has-full-text")
    has_funder: bool | None = Field(None, alias="has-funder")
    has_funder_doi: bool | None = Field(None, alias="has-funder-doi")
    has_funder_ror_id: bool | None = Field(None, alias="has-funder-ror-id")
    has_license: bool | None = Field(None, alias="has-license")
    has_orcid: bool | None = Field(None, alias="has-orcid")
    has_prime_doi: bool | None = Field(None, alias="has-prime-doi")
    has_references: bool | None = Field(None, alias="has-references")
    has_relation: bool | None = Field(None, alias="has-relation")
    has_ror_id: bool | None = Field(None, alias="has-ror-id")
    has_update: bool | None = Field(None, alias="has-update")
    has_update_policy: bool | None = Field(None, alias="has-update-policy")
    has_alias: bool | None = Field(None, alias="has-alias")


class MemberFilters(_CrossrefFilters):
    """Filter model for ``/members`` (probe-verified 2026-11)."""

    prefix: str | None = None
    backfile_doi_count: str | None = Field(None, alias="backfile-doi-count")
    current_doi_count: str | None = Field(None, alias="current-doi-count")


class FunderFilters(_CrossrefFilters):
    """Filter model for ``/funders``; ``location`` is a case-sensitive country name."""

    location: str | None = None


__all__ = ["FunderFilters", "MemberFilters", "WorksFilters"]
