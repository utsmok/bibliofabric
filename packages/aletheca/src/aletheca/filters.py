"""Pydantic filter models for the OpenAlex API.

Each model maps to the ``filter=field:value,field:value`` syntax of one
entity's list endpoint. Nested fields use dot-notation aliases. Every model
allows extra fields, so filters added upstream stay usable before they land
here.

Deprecated and paid filters are deliberately absent:

- ``concepts.id`` / ``x_concepts.id``: deprecated aliases of ``topics.id``.
- ``default.search``: alias of ``fulltext.search``.
- ``is_xpac`` / ``include_xpac``: legacy corpus controls; use the ``corpus``
  parameter (they 400 when combined with ``corpus=``).
- ``from/to_created_date``, ``from/to_updated_date`` on works: paid
  (Member+/Partner daily sync; free accounts get 403 "Plan upgrade required").
- ``is_in_jstage*`` on sources: no longer returned or documented upstream.
- ``parent_works.relationship``: renamed ``parent_works.link_type`` by
  OpenAlex (2026-11-14); the old filter name errors after 2027-03-01.
"""

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field

_SharedConfig = ConfigDict(extra="allow", populate_by_name=True)

StrFilter = str | Sequence[str] | None
IntFilter = int | str | Sequence[int | str] | None
FloatFilter = float | int | str | Sequence[float | int | str] | None


class WorksFilters(BaseModel):
    """Filter model for the works endpoint."""

    publication_year: IntFilter = None
    publication_date: StrFilter = None
    from_publication_date: StrFilter = None
    to_publication_date: StrFilter = None
    type: StrFilter = None
    is_oa: bool | None = None
    doi: StrFilter = None
    pmid: StrFilter = None
    pmcid: StrFilter = None
    language: StrFilter = None
    cites: StrFilter = None
    cited_by: StrFilter = None
    related_to: StrFilter = None
    indexed_in: StrFilter = None

    # Nested filter fields (dot notation via alias)
    authorships_author_id: StrFilter = Field(None, alias="authorships.author.id")
    authorships_institutions_id: StrFilter = Field(
        None, alias="authorships.institutions.id"
    )
    topics_id: StrFilter = Field(None, alias="topics.id")
    keywords_id: StrFilter = Field(None, alias="keywords.id")
    funders_id: StrFilter = Field(None, alias="funders.id")
    awards_id: StrFilter = Field(None, alias="awards.id")
    awards_funder_id: StrFilter = Field(None, alias="awards.funder_id")
    awards_funder_award_id: StrFilter = Field(None, alias="awards.funder_award_id")
    primary_location_source_id: StrFilter = Field(
        None, alias="primary_location.source.id"
    )
    primary_location_source_type: StrFilter = Field(
        None, alias="primary_location.source.type"
    )
    primary_location_source_has_issn: bool | None = Field(
        None, alias="primary_location.source.has_issn"
    )
    primary_location_is_oa: bool | None = Field(None, alias="primary_location.is_oa")
    locations_is_oa: bool | None = Field(None, alias="locations.is_oa")
    locations_source_id: StrFilter = Field(None, alias="locations.source.id")
    locations_source_type: StrFilter = Field(None, alias="locations.source.type")
    locations_source_has_issn: bool | None = Field(
        None, alias="locations.source.has_issn"
    )

    # Search filters. Deprecated upstream in favor of the ``search`` /
    # ``search.*`` parameters (see WorksClient.search_scoped); still served.
    title_search: StrFilter = Field(None, alias="title.search")
    abstract_search: StrFilter = Field(None, alias="abstract.search")
    fulltext_search: StrFilter = Field(None, alias="fulltext.search")
    display_name_search: StrFilter = Field(None, alias="display_name.search")
    title_and_abstract_search: StrFilter = Field(
        None, alias="title_and_abstract.search"
    )
    raw_affiliation_strings_search: StrFilter = Field(
        None, alias="raw_affiliation_strings.search"
    )

    # Boolean presence filters
    has_doi: bool | None = None
    has_pmid: bool | None = None
    has_pmcid: bool | None = None
    has_orcid: bool | None = None
    has_abstract: bool | None = None
    has_fulltext: bool | None = None
    has_references: bool | None = None
    has_oa_accepted_or_published_version: bool | None = Field(
        None, alias="has_oa_accepted_or_published_version"
    )
    has_oa_submitted_version: bool | None = Field(
        None, alias="has_oa_submitted_version"
    )

    # Count / attribute filters
    authors_count: IntFilter = None
    best_open_version: StrFilter = None
    best_oa_version: StrFilter = None
    version: StrFilter = None
    cited_by_count: IntFilter = None
    fwci: FloatFilter = None
    oa_status: StrFilter = None
    is_retracted: bool | None = None
    is_pulled: bool | None = None
    pull_notice_works_id: StrFilter = Field(None, alias="pull_notice_works.id")
    pull_notice_works_link_type: StrFilter = Field(
        None, alias="pull_notice_works.link_type"
    )
    is_paratext: bool | None = None
    referenced_works: StrFilter = None

    # Part-of (parent/child works) filters
    has_parent_work: bool | None = Field(None, alias="has_parent_work")
    parent_works_id: StrFilter = Field(None, alias="parent_works.id")
    parent_works_link_type: StrFilter = Field(None, alias="parent_works.link_type")
    lineage: StrFilter = None
    child_works_count: IntFilter = None
    is_traditional: bool | None = None

    model_config = _SharedConfig


class AuthorsFilters(BaseModel):
    """Filter model for the authors endpoint."""

    orcid: StrFilter = None
    display_name: StrFilter = None
    works_count: IntFilter = None
    cited_by_count: IntFilter = None
    topics_id: StrFilter = Field(None, alias="topics.id")

    # Nested filter fields (dot notation via alias)
    affiliation_institution_id: StrFilter = Field(
        None, alias="affiliations.institution.id"
    )
    last_known_institutions_id: StrFilter = Field(
        None, alias="last_known_institutions.id"
    )
    display_name_search: StrFilter = Field(None, alias="display_name.search")

    # Boolean / presence filters
    has_orcid: bool | None = None

    # Nested institution filters
    affiliations_institution_country_code: StrFilter = Field(
        None, alias="affiliations.institution.country_code"
    )
    affiliations_institution_lineage: StrFilter = Field(
        None, alias="affiliations.institution.lineage"
    )
    affiliations_institution_ror: StrFilter = Field(
        None, alias="affiliations.institution.ror"
    )
    affiliations_institution_type: StrFilter = Field(
        None, alias="affiliations.institution.type"
    )
    last_known_institutions_country_code: StrFilter = Field(
        None, alias="last_known_institutions.country_code"
    )
    last_known_institutions_lineage: StrFilter = Field(
        None, alias="last_known_institutions.lineage"
    )
    last_known_institutions_ror: StrFilter = Field(
        None, alias="last_known_institutions.ror"
    )
    last_known_institutions_type: StrFilter = Field(
        None, alias="last_known_institutions.type"
    )
    last_known_institutions_continent: StrFilter = Field(
        None, alias="last_known_institutions.continent"
    )
    last_known_institutions_is_global_south: bool | None = Field(
        None, alias="last_known_institutions.is_global_south"
    )

    # ID and summary stats filters
    ids_openalex: StrFilter = Field(None, alias="ids.openalex")
    summary_stats_2yr_mean_citedness: FloatFilter = Field(
        None, alias="summary_stats.2yr_mean_citedness"
    )
    summary_stats_h_index: IntFilter = Field(None, alias="summary_stats.h_index")
    summary_stats_i10_index: IntFilter = Field(None, alias="summary_stats.i10_index")
    block_key: StrFilter = None

    model_config = _SharedConfig


class SourcesFilters(BaseModel):
    """Filter model for the sources endpoint."""

    display_name: StrFilter = None
    type: StrFilter = None
    is_oa: bool | None = None
    host_organization: StrFilter = None
    issn: StrFilter = None
    issn_l: StrFilter = Field(None, alias="issn_l")
    has_apc: bool | None = None
    works_count: IntFilter = None
    works_count_range: StrFilter = None
    cited_by_count: IntFilter = None
    cited_by_count_range: StrFilter = None
    display_name_search: StrFilter = Field(None, alias="display_name.search")
    continent: StrFilter = None
    has_issn: bool | None = None
    is_global_south: bool | None = None
    summary_stats_2yr_mean_citedness: FloatFilter = Field(
        None, alias="summary_stats.2yr_mean_citedness"
    )
    summary_stats_h_index: IntFilter = Field(None, alias="summary_stats.h_index")
    summary_stats_i10_index: IntFilter = Field(None, alias="summary_stats.i10_index")

    model_config = _SharedConfig


class InstitutionsFilters(BaseModel):
    """Filter model for the institutions endpoint."""

    display_name: StrFilter = None
    country_code: StrFilter = None
    type: StrFilter = None
    ror: StrFilter = None
    works_count: IntFilter = None
    works_count_range: StrFilter = None
    cited_by_count: IntFilter = None
    cited_by_count_range: StrFilter = None
    display_name_search: StrFilter = Field(None, alias="display_name.search")
    continent: StrFilter = None
    is_global_south: bool | None = None
    has_ror: bool | None = None
    is_super_system: bool | None = None

    model_config = _SharedConfig


class TopicsFilters(BaseModel):
    """Filter model for the topics endpoint."""

    display_name: StrFilter = None
    id: StrFilter = None
    subfield_id: StrFilter = Field(None, alias="subfield.id")
    field_id: StrFilter = Field(None, alias="field.id")
    domain_id: StrFilter = Field(None, alias="domain.id")
    works_count: IntFilter = None
    works_count_range: StrFilter = None
    display_name_search: StrFilter = Field(None, alias="display_name.search")
    keywords_search: StrFilter = Field(None, alias="keywords.search")
    keywords_id: StrFilter = Field(None, alias="keywords.id")
    keywords_keyword: StrFilter = Field(None, alias="keywords.keyword")
    keywords_display_name: StrFilter = Field(None, alias="keywords.display_name")

    model_config = _SharedConfig


class KeywordsFilters(BaseModel):
    """Filter model for the keywords endpoint."""

    display_name: StrFilter = None
    works_count: IntFilter = None
    works_count_range: StrFilter = None
    display_name_search: StrFilter = Field(None, alias="display_name.search")

    model_config = _SharedConfig


class PublishersFilters(BaseModel):
    """Filter model for the publishers endpoint."""

    display_name: StrFilter = None
    country_codes: StrFilter = None
    hierarchy_level: IntFilter = None
    works_count: IntFilter = None
    works_count_range: StrFilter = None
    display_name_search: StrFilter = Field(None, alias="display_name.search")
    continent: StrFilter = None
    lineage: StrFilter = None
    ror: StrFilter = None

    model_config = _SharedConfig


class FundersFilters(BaseModel):
    """Filter model for the funders endpoint."""

    display_name: StrFilter = None
    country_code: StrFilter = None
    ror: StrFilter = None
    works_count: IntFilter = None
    works_count_range: StrFilter = None
    display_name_search: StrFilter = Field(None, alias="display_name.search")
    awards_count: IntFilter = None
    continent: StrFilter = None
    is_global_south: bool | None = None
    summary_stats_2yr_mean_citedness: FloatFilter = Field(
        None, alias="summary_stats.2yr_mean_citedness"
    )
    summary_stats_h_index: IntFilter = Field(None, alias="summary_stats.h_index")
    summary_stats_i10_index: IntFilter = Field(None, alias="summary_stats.i10_index")

    model_config = _SharedConfig


class AwardsFilters(BaseModel):
    """Filter model for the awards endpoint.

    Aliases follow the live API's valid-filter list, which the API
    enumerates in the 400 error returned for invalid fields.
    ``funder.country_code``, ``lead_investigator.id``,
    ``co_lead_investigator.id``, plain ``funder`` and ``display_name``,
    and ``from_/to_*_date`` range filters are NOT valid on this endpoint
    and are absent here; ``extra="allow"`` still lets callers pass
    anything else.
    """

    id: StrFilter = None
    doi: StrFilter = None
    funder_name: StrFilter = None
    funder_award_id: StrFilter = None
    funder_scheme: StrFilter = None
    funding_type: StrFilter = None
    provenance: StrFilter = None
    collection: StrFilter = None
    currency: StrFilter = None
    amount: FloatFilter = None
    start_year: IntFilter = None
    end_year: IntFilter = None
    funded_outputs: StrFilter = None
    funded_outputs_count: IntFilter = None

    # Nested filter fields (dot notation via alias)
    funder_id: StrFilter = Field(None, alias="funder.id")
    funder_ror: StrFilter = Field(None, alias="funder.ror")
    funder_doi: StrFilter = Field(None, alias="funder.doi")
    lead_investigator_orcid: StrFilter = Field(None, alias="lead_investigator.orcid")
    lead_investigator_given_name: StrFilter = Field(
        None, alias="lead_investigator.given_name"
    )
    lead_investigator_family_name: StrFilter = Field(
        None, alias="lead_investigator.family_name"
    )
    lead_investigator_affiliation_name: StrFilter = Field(
        None, alias="lead_investigator.affiliation.name"
    )
    lead_investigator_affiliation_country: StrFilter = Field(
        None, alias="lead_investigator.affiliation.country"
    )
    institution_awarded_id: StrFilter = Field(None, alias="institution_awarded.id")
    institution_awarded_ror: StrFilter = Field(None, alias="institution_awarded.ror")
    institution_awarded_country_code: StrFilter = Field(
        None, alias="institution_awarded.country_code"
    )
    institution_awarded_type: StrFilter = Field(None, alias="institution_awarded.type")
    institution_awarded_lineage: StrFilter = Field(
        None, alias="institution_awarded.lineage"
    )
    institution_awarded_continent: StrFilter = Field(
        None, alias="institution_awarded.continent"
    )
    primary_topic_id: StrFilter = Field(None, alias="primary_topic.id")
    primary_topic_subfield_id: StrFilter = Field(
        None, alias="primary_topic.subfield.id"
    )
    primary_topic_field_id: StrFilter = Field(None, alias="primary_topic.field.id")
    primary_topic_domain_id: StrFilter = Field(None, alias="primary_topic.domain.id")
    topics_id: StrFilter = Field(None, alias="topics.id")
    topics_subfield_id: StrFilter = Field(None, alias="topics.subfield.id")
    topics_field_id: StrFilter = Field(None, alias="topics.field.id")
    topics_domain_id: StrFilter = Field(None, alias="topics.domain.id")

    # Search filters
    display_name_search: StrFilter = Field(None, alias="display_name.search")
    description_search: StrFilter = Field(None, alias="description.search")
    text_search: StrFilter = Field(None, alias="text.search")

    model_config = _SharedConfig


class LocationsFilters(BaseModel):
    """Filter model for the ``/locations`` per-copy index endpoint."""

    id: StrFilter = None
    work_id: StrFilter = None
    doi: StrFilter = None
    native_id: StrFilter = None
    native_id_namespace: StrFilter = None
    provenance: StrFilter = None
    source_id: StrFilter = None
    type: StrFilter = None
    raw_type: StrFilter = None
    language: StrFilter = None
    is_oa: bool | None = None
    is_retracted: bool | None = None
    version: StrFilter = None
    license: StrFilter = None
    publisher: StrFilter = None

    model_config = _SharedConfig


class LinksFilters(BaseModel):
    """Filter model for the ``/links`` work-edge endpoint."""

    origin: StrFilter = None
    target: StrFilter = None
    link_type: StrFilter = None

    model_config = _SharedConfig
