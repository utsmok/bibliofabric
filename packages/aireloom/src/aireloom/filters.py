"""Filter models for the OpenAIRE Graph V4 filter-based queries, the Graph
links route, and the Scholexplorer API.

The five entity filter models describe the V4 single ``filter=`` expression:
each attribute becomes one ``field:value`` entry (comma is AND, ``|`` is OR
within a field, ``!`` negates, and ``>``/``<`` compare). Dotted V4 field names
are expressed through pydantic aliases (``ids_doi`` sends ``ids.doi``). The
``LinksFilters`` and ``ScholixFilters`` models instead map one attribute to
one query parameter, as those routes accept individual parameters.
"""

from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any, Literal

from bibliofabric.exceptions import ConfigurationError
from pydantic import BaseModel, ConfigDict, Field

from .dialect import MAX_OR_VALUES

V4_ENTITY_TYPES = Literal["publication", "dataset", "software", "other"]
V4_PROJECT_STATUS = Literal["completed", "ongoing", "planned"]

type StrFilter = str | Sequence[str]
type DateFilter = date | str
type NumericFilter = int | str | Sequence[int | str]


def encode_filter_value(value: Any, *, field: str | None = None) -> str:
    """Encode one filter value: booleans, dates, and OR-sequences become strings.

    Strings pass through untouched so range operators such as ``">100"`` or
    negations such as ``"!other"`` survive verbatim. Enforces the OpenAIRE V4
    per-field cap of 50 pipe-separated OR values.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        items = [encode_filter_value(entry, field=field) for entry in value]
        items = [item for item in items if item]
        if len(items) > MAX_OR_VALUES:
            label = f"Filter field {field!r}" if field else "Filter field"
            raise ConfigurationError(
                f"{label} has {len(items)} OR values; OpenAIRE V4 accepts at most "
                f"{MAX_OR_VALUES} pipe-separated values per field."
            )
        return "|".join(items)
    rendered = str(value)
    if "|" in rendered:
        parts = rendered.split("|")
        if len(parts) > MAX_OR_VALUES:
            label = f"Filter field {field!r}" if field else "Filter field"
            raise ConfigurationError(
                f"{label} has {len(parts)} OR values; OpenAIRE V4 accepts at most "
                f"{MAX_OR_VALUES} pipe-separated values per field."
            )
    return rendered


def encode_filter_mapping(items: Mapping[str, Any]) -> str:
    """Serialize a mapping of ``field -> value`` into one V4 ``filter`` string.

    ``None`` entries and empty sequences are omitted so invalid ``field:``
    predicates are never sent.
    """
    parts: list[str] = []
    for field, value in items.items():
        if value is None:
            continue
        if (
            isinstance(value, Sequence)
            and not isinstance(value, str | bytes)
            and not value
        ):
            continue
        encoded = encode_filter_value(value, field=field)
        if not encoded:
            continue
        parts.append(f"{field}:{encoded}")
    return ",".join(parts)


class GraphFilters(BaseModel):
    """Base class for V4 entity filter models."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    def to_expression(self) -> str:
        """Dump the set fields into one V4 ``filter`` expression."""
        dumped = self.model_dump(exclude_none=True, by_alias=True)
        return encode_filter_mapping(dumped)


class ResearchProductsFilters(GraphFilters):
    """V4 filters for ``/v4/research-products``.

    Value strings may carry the operators the API accepts: a leading ``!``
    negates, ``>``/``<`` compare on date and numeric fields such as
    ``impact_citation_count``, sequences join with ``|`` for OR within a field
    (up to 50 values), and ``from_``/``to_`` pairs bound ranges.
    """

    id: StrFilter | None = None
    ids_doi: StrFilter | None = Field(default=None, alias="ids.doi")
    ids_pmid: StrFilter | None = Field(default=None, alias="ids.pmid")
    ids_pmcid: StrFilter | None = Field(default=None, alias="ids.pmcid")
    ids_arxiv: StrFilter | None = Field(default=None, alias="ids.arxiv")
    ids_handle: StrFilter | None = Field(default=None, alias="ids.handle")
    ids_original: StrFilter | None = Field(default=None, alias="ids.original")
    ids_pid: StrFilter | None = Field(default=None, alias="ids.pid")
    type: V4_ENTITY_TYPES | str | Sequence[str] | None = None
    instance_type: StrFilter | None = None
    subjects: StrFilter | None = None
    sdg: StrFilter | None = None
    fos: StrFilter | None = None
    from_publication_date: DateFilter | None = None
    to_publication_date: DateFilter | None = None
    from_publication_year: int | None = None
    to_publication_year: int | None = None
    date_of_collection: DateFilter | None = None
    title_search: str | None = Field(default=None, alias="title.search")
    abstract_search: str | None = Field(default=None, alias="abstract.search")
    title_and_abstract_search: str | None = Field(
        default=None, alias="title_and_abstract.search"
    )
    default_search: str | None = Field(default=None, alias="default.search")
    authorships_author_fullname: StrFilter | None = Field(
        default=None, alias="authorships.author.fullname"
    )
    authorships_author_orcid: StrFilter | None = Field(
        default=None, alias="authorships.author.orcid"
    )
    authorships_institutions_ror: StrFilter | None = Field(
        default=None, alias="authorships.institutions.ror"
    )
    authorships_countries: StrFilter | None = Field(
        default=None, alias="authorships.countries"
    )
    authorships_continent: StrFilter | None = Field(
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
    best_oa_rights: StrFilter | None = Field(default=None, alias="best_oa.rights")
    oa_color: StrFilter | None = None
    is_green: bool | None = None
    is_peer_reviewed: bool | None = None
    is_in_diamond_journal: bool | None = None
    is_publicly_funded: bool | None = None
    impact_influence_class: StrFilter | None = Field(
        default=None, alias="impact.influence_class"
    )
    impact_popularity_class: StrFilter | None = Field(
        default=None, alias="impact.popularity_class"
    )
    impact_impulse_class: StrFilter | None = Field(
        default=None, alias="impact.impulse_class"
    )
    impact_citation_count_class: StrFilter | None = Field(
        default=None, alias="impact.citation_count_class"
    )
    impact_citation_count: int | str | None = Field(
        default=None, alias="impact.citation_count"
    )
    publisher: StrFilter | None = None
    host_datasource_id: StrFilter | None = Field(
        default=None, alias="host_datasource.id"
    )
    collected_from_id: StrFilter | None = Field(default=None, alias="collected_from.id")
    grants_project_id: StrFilter | None = Field(default=None, alias="grants.project_id")
    grants_code: StrFilter | None = Field(default=None, alias="grants.code")
    grants_funder_short_name: StrFilter | None = Field(
        default=None, alias="grants.funder_short_name"
    )
    grants_funding_stream_id: StrFilter | None = Field(
        default=None, alias="grants.funding_stream_id"
    )
    affiliations_organization_id: StrFilter | None = Field(
        default=None, alias="affiliations.organization_id"
    )
    communities_id: StrFilter | None = Field(default=None, alias="communities.id")
    language: StrFilter | None = None


class ProjectsFilters(GraphFilters):
    """V4 filters for ``/v4/projects``."""

    id: StrFilter | None = None
    code: StrFilter | None = None
    acronym: StrFilter | None = None
    pid: StrFilter | None = None
    call_identifier: StrFilter | None = None
    project_status: V4_PROJECT_STATUS | str | Sequence[str] | None = None
    title_search: str | None = Field(default=None, alias="title.search")
    keywords_search: str | None = Field(default=None, alias="keywords.search")
    default_search: str | None = Field(default=None, alias="default.search")
    funder: StrFilter | None = None
    funder_short_name: StrFilter | None = None
    funding_stream_id: StrFilter | None = None
    funding_level_0_id: StrFilter | None = None
    funding_level_1_id: StrFilter | None = None
    funding_level_2_id: StrFilter | None = None
    country: StrFilter | None = None
    continent: StrFilter | None = None
    is_global_south: bool | None = None
    oa_mandate_publications: bool | None = None
    from_start_date: DateFilter | None = None
    to_start_date: DateFilter | None = None
    from_end_date: DateFilter | None = None
    to_end_date: DateFilter | None = None
    start_year: NumericFilter | None = None
    end_year: NumericFilter | None = None
    active_year: NumericFilter | None = None
    organizations_id: StrFilter | None = Field(default=None, alias="organizations.id")
    organizations_name: StrFilter | None = Field(
        default=None, alias="organizations.name"
    )
    organizations_country: StrFilter | None = Field(
        default=None, alias="organizations.country"
    )
    communities_id: StrFilter | None = Field(default=None, alias="communities.id")
    collected_from_id: StrFilter | None = Field(default=None, alias="collected_from.id")


class OrganizationsFilters(GraphFilters):
    """V4 filters for ``/v4/organizations``."""

    id: StrFilter | None = None
    pid: StrFilter | None = None
    legal_name_search: str | None = Field(default=None, alias="legal_name.search")
    legal_short_name_search: str | None = Field(
        default=None, alias="legal_short_name.search"
    )
    default_search: str | None = Field(default=None, alias="default.search")
    country: StrFilter | None = None
    continent: StrFilter | None = None
    is_global_south: bool | None = None
    communities_id: StrFilter | None = Field(default=None, alias="communities.id")
    collected_from_id: StrFilter | None = Field(default=None, alias="collected_from.id")


class DataSourcesFilters(GraphFilters):
    """V4 filters for ``/v4/datasources``."""

    id: StrFilter | None = None
    pid: StrFilter | None = None
    official_name_search: str | None = Field(default=None, alias="official_name.search")
    english_name_search: str | None = Field(default=None, alias="english_name.search")
    default_search: str | None = Field(default=None, alias="default.search")
    type: StrFilter | None = None
    subjects: StrFilter | None = None
    content_types: StrFilter | None = None
    eosc_datasource_type: StrFilter | None = None
    jurisdiction: StrFilter | None = None
    thematic: bool | None = None
    od_languages: StrFilter | None = None
    country: StrFilter | None = None
    continent: StrFilter | None = None
    is_global_south: bool | None = None
    compatibility_id: StrFilter | None = Field(default=None, alias="compatibility.id")
    compatibility_name: StrFilter | None = Field(
        default=None, alias="compatibility.name"
    )
    organizations_id: StrFilter | None = Field(default=None, alias="organizations.id")
    communities_id: StrFilter | None = Field(default=None, alias="communities.id")
    collected_from_id: StrFilter | None = Field(default=None, alias="collected_from.id")
    collected_from_name: StrFilter | None = Field(
        default=None, alias="collected_from.name"
    )


class PersonsFilters(GraphFilters):
    """V4 filters for ``/v4/persons``."""

    id: StrFilter | None = None
    ids_original: StrFilter | None = Field(default=None, alias="ids.original")
    given_name: StrFilter | None = None
    last_name: StrFilter | None = None
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
    fromDate: DateFilter | None = Field(default=None, description="YYYY or YYYY-MM-DD")
    toDate: DateFilter | None = Field(default=None, description="YYYY or YYYY-MM-DD")


class ScholixFilters(BaseModel):
    """Query parameters for the Scholexplorer ``Links`` endpoints (V3 and V2).

    One of ``sourcePid``, ``targetPid``, ``sourcePublisher``,
    ``targetPublisher``, ``sourceType``, or ``targetType`` is required.
    ``linkProvider`` is supported on V2 only (V3 silently ignores it), so
    queries carrying ``linkProvider`` are routed to V2 automatically. Note that
    V3 returns zero rows for ``from``/``to`` date filters and V2 ignores date
    parameters (see ``docs/aireloom/quirks.md``).
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
    from_date: DateFilter | None = Field(
        default=None, alias="from", description="YYYY or YYYY-MM-DD"
    )
    to_date: DateFilter | None = Field(
        default=None, alias="to", description="YYYY or YYYY-MM-DD"
    )


__all__ = [
    "DataSourcesFilters",
    "DateFilter",
    "GraphFilters",
    "LinksFilters",
    "NumericFilter",
    "OrganizationsFilters",
    "PersonsFilters",
    "ProjectsFilters",
    "ResearchProductsFilters",
    "ScholixFilters",
    "StrFilter",
    "encode_filter_mapping",
    "encode_filter_value",
]
