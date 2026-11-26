"""Filter models for the OpenAIRE Graph V4 filter-based queries, the Graph
links route, and the Scholexplorer API.

The five entity filter models describe the V4 single ``filter=`` expression:
each attribute becomes one ``field:value`` entry (comma is AND, ``|`` is OR
within a field, ``!`` negates, and ``>``/``<`` compare). Dotted V4 field names
are expressed through pydantic aliases (``ids_doi`` sends ``ids.doi``). The
``LinksFilters`` and ``ScholixFilters`` models instead map one attribute to
one query parameter, as those routes accept individual parameters.
"""

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

V4_ENTITY_TYPES = Literal["publication", "dataset", "software", "other"]
V4_PROJECT_STATUS = Literal["completed", "ongoing", "planned"]


def encode_filter_value(value: Any) -> str:
    """Encode one filter value: booleans, dates, and OR-lists become strings.

    Strings pass through untouched so range operators such as ``">100"`` or
    quoted values survive verbatim.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, list | tuple):
        return "|".join(encode_filter_value(entry) for entry in value)
    return str(value)


class GraphFilters(BaseModel):
    """Base class for V4 entity filter models."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    def to_expression(self) -> str:
        """Dump the set fields into one V4 ``filter`` expression."""
        dumped = self.model_dump(exclude_none=True, by_alias=True)
        return ",".join(
            f"{field}:{encode_filter_value(value)}" for field, value in dumped.items()
        )


class ResearchProductsFilters(GraphFilters):
    """V4 filters for ``/v4/research-products``.

    Value strings may carry the operators the API accepts: a leading ``!``
    negates, ``>``/``<`` compare on date and numeric fields such as
    ``impact_citation_count``, and ``from_``/``to_`` pairs bound ranges.
    """

    id: str | None = None
    ids_doi: str | None = Field(default=None, alias="ids.doi")
    ids_pmid: str | None = Field(default=None, alias="ids.pmid")
    ids_pmcid: str | None = Field(default=None, alias="ids.pmcid")
    ids_arxiv: str | None = Field(default=None, alias="ids.arxiv")
    ids_handle: str | None = Field(default=None, alias="ids.handle")
    ids_original: str | None = Field(default=None, alias="ids.original")
    ids_pid: str | None = Field(default=None, alias="ids.pid")
    type: V4_ENTITY_TYPES | None = None
    instance_type: str | None = None
    subjects: list[str] | None = None
    sdg: list[str] | None = None
    fos: list[str] | None = None
    from_publication_date: str | None = None
    to_publication_date: str | None = None
    from_publication_year: int | None = None
    to_publication_year: int | None = None
    date_of_collection: str | None = None
    title_search: str | None = Field(default=None, alias="title.search")
    abstract_search: str | None = Field(default=None, alias="abstract.search")
    title_and_abstract_search: str | None = Field(
        default=None, alias="title_and_abstract.search"
    )
    default_search: str | None = Field(default=None, alias="default.search")
    authorships_author_fullname: str | None = Field(
        default=None, alias="authorships.author.fullname"
    )
    authorships_author_orcid: str | None = Field(
        default=None, alias="authorships.author.orcid"
    )
    authorships_institutions_ror: str | None = Field(
        default=None, alias="authorships.institutions.ror"
    )
    authorships_countries: list[str] | None = Field(
        default=None, alias="authorships.countries"
    )
    authorships_continent: str | None = Field(
        default=None, alias="authorships.continent"
    )
    authorships_is_global_south: bool | None = Field(
        default=None, alias="authorships.is_global_south"
    )
    has_doi: bool | None = None
    has_pmid: bool | None = None
    has_pmcid: bool | None = None
    has_arxiv: bool | None = None
    has_handle: bool | None = None
    has_orcid: bool | None = None
    has_abstract: bool | None = None
    has_grant: bool | None = None
    has_license: bool | None = None
    best_oa_rights: str | None = Field(default=None, alias="best_oa.rights")
    oa_color: str | None = None
    is_green: bool | None = None
    is_peer_reviewed: bool | None = None
    is_in_diamond_journal: bool | None = None
    is_publicly_funded: bool | None = None
    impact_influence_class: str | None = Field(
        default=None, alias="impact.influence_class"
    )
    impact_popularity_class: str | None = Field(
        default=None, alias="impact.popularity_class"
    )
    impact_impulse_class: str | None = Field(default=None, alias="impact.impulse_class")
    impact_citation_count_class: str | None = Field(
        default=None, alias="impact.citation_count_class"
    )
    impact_citation_count: str | None = Field(
        default=None, alias="impact.citation_count"
    )
    publisher: str | None = None
    host_datasource_id: str | None = Field(default=None, alias="host_datasource.id")
    collected_from_id: str | None = Field(default=None, alias="collected_from.id")
    grants_project_id: str | None = Field(default=None, alias="grants.project_id")
    grants_code: str | None = Field(default=None, alias="grants.code")
    grants_funder_short_name: str | None = Field(
        default=None, alias="grants.funder_short_name"
    )
    grants_funding_stream_id: str | None = Field(
        default=None, alias="grants.funding_stream_id"
    )
    affiliations_organization_id: str | None = Field(
        default=None, alias="affiliations.organization_id"
    )
    communities_id: str | None = Field(default=None, alias="communities.id")
    language: str | None = None


class ProjectsFilters(GraphFilters):
    """V4 filters for ``/v4/projects``."""

    id: str | None = None
    code: str | None = None
    acronym: str | None = None
    pid: str | None = None
    call_identifier: str | None = None
    project_status: V4_PROJECT_STATUS | None = None
    title_search: str | None = Field(default=None, alias="title.search")
    keywords_search: str | None = Field(default=None, alias="keywords.search")
    default_search: str | None = Field(default=None, alias="default.search")
    funder: str | None = None
    funder_short_name: str | None = None
    funding_stream_id: str | None = None
    funding_level_0_id: str | None = None
    funding_level_1_id: str | None = None
    funding_level_2_id: str | None = None
    country: str | None = None
    continent: str | None = None
    is_global_south: bool | None = None
    oa_mandate_publications: bool | None = None
    from_start_date: str | None = None
    to_start_date: str | None = None
    from_end_date: str | None = None
    to_end_date: str | None = None
    start_year: str | None = None
    end_year: str | None = None
    active_year: str | None = None
    organizations_id: str | None = Field(default=None, alias="organizations.id")
    organizations_name: str | None = Field(default=None, alias="organizations.name")
    organizations_country: str | None = Field(
        default=None, alias="organizations.country"
    )
    communities_id: str | None = Field(default=None, alias="communities.id")
    collected_from_id: str | None = Field(default=None, alias="collected_from.id")


class OrganizationsFilters(GraphFilters):
    """V4 filters for ``/v4/organizations``."""

    id: str | None = None
    pid: str | None = None
    legal_name_search: str | None = Field(default=None, alias="legal_name.search")
    legal_short_name_search: str | None = Field(
        default=None, alias="legal_short_name.search"
    )
    default_search: str | None = Field(default=None, alias="default.search")
    country: str | None = None
    continent: str | None = None
    is_global_south: bool | None = None
    communities_id: str | None = Field(default=None, alias="communities.id")
    collected_from_id: str | None = Field(default=None, alias="collected_from.id")


class DataSourcesFilters(GraphFilters):
    """V4 filters for ``/v4/datasources``."""

    id: str | None = None
    pid: str | None = None
    official_name_search: str | None = Field(default=None, alias="official_name.search")
    english_name_search: str | None = Field(default=None, alias="english_name.search")
    default_search: str | None = Field(default=None, alias="default.search")
    type: str | None = None
    subjects: list[str] | None = None
    content_types: list[str] | None = None
    eosc_datasource_type: str | None = None
    jurisdiction: str | None = None
    thematic: bool | None = None
    od_languages: str | None = None
    country: str | None = None
    continent: str | None = None
    is_global_south: bool | None = None
    compatibility_id: str | None = Field(default=None, alias="compatibility.id")
    compatibility_name: str | None = Field(default=None, alias="compatibility.name")
    organizations_id: str | None = Field(default=None, alias="organizations.id")
    communities_id: str | None = Field(default=None, alias="communities.id")
    collected_from_id: str | None = Field(default=None, alias="collected_from.id")
    collected_from_name: str | None = Field(default=None, alias="collected_from.name")


class PersonsFilters(GraphFilters):
    """V4 filters for ``/v4/persons``."""

    id: str | None = None
    ids_original: str | None = Field(default=None, alias="ids.original")
    given_name: str | None = None
    last_name: str | None = None
    default_search: str | None = Field(default=None, alias="default.search")


class LinksFilters(BaseModel):
    """Query parameters for the Graph ``/v3/research-products/links`` route.

    This route takes individual parameters (not the V4 filter expression), so
    each attribute maps to one query parameter.
    """

    model_config = ConfigDict(extra="forbid")

    sourcePid: str | None = Field(
        default=None, description="Source persistent identifier, e.g. a DOI"
    )
    targetPid: str | None = Field(
        default=None, description="Target persistent identifier"
    )
    sourcePublisher: str | None = Field(
        default=None, description="Source publisher name"
    )
    targetPublisher: str | None = Field(
        default=None, description="Target publisher name"
    )
    sourceType: V4_ENTITY_TYPES | None = None
    targetType: V4_ENTITY_TYPES | None = None
    relation: str | None = Field(
        default=None, description="Relationship type, e.g. IsSupplementTo"
    )
    fromDate: str | None = Field(default=None, description="YYYY or YYYY-MM-DD")
    toDate: str | None = Field(default=None, description="YYYY or YYYY-MM-DD")


class ScholixFilters(BaseModel):
    """Query parameters for the Scholexplorer ``Links`` endpoints (V3 and V2).

    One of ``sourcePid``, ``targetPid``, ``sourcePublisher``,
    ``targetPublisher``, ``sourceType``, or ``targetType`` is required.
    ``linkProvider`` is accepted by both versions; the date filters route to
    V2 automatically because V3 returns zero rows for them (OA-4).
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    sourcePid: str | None = None
    targetPid: str | None = None
    sourcePublisher: str | None = None
    targetPublisher: str | None = None
    sourceType: Literal["Publication", "Dataset", "Software", "Other"] | None = None
    targetType: Literal["Publication", "Dataset", "Software", "Other"] | None = None
    relation: str | None = None
    linkProvider: str | None = None
    from_date: str | None = Field(
        default=None, alias="from", description="YYYY or YYYY-MM-DD"
    )
    to_date: str | None = Field(
        default=None, alias="to", description="YYYY or YYYY-MM-DD"
    )


__all__ = [
    "DataSourcesFilters",
    "GraphFilters",
    "LinksFilters",
    "OrganizationsFilters",
    "PersonsFilters",
    "ProjectsFilters",
    "ResearchProductsFilters",
    "ScholixFilters",
    "encode_filter_value",
]
