"""Pydantic filter models for the DataCite REST API.

Each field maps to one query parameter of its route. Only parameters that
change the answer anonymously are typed (checked against the live API and the
DataCite reference on 2026-11-28). A value that is a sequence joins its items
with a comma, which DataCite reads as ``OR``; different keys ``AND``. Every
model allows extra fields, so filters added upstream stay usable before they
land here.

The API silently ignores unknown query parameters, so a misspelled filter
changes nothing instead of failing; prefer the typed fields. A parameter that
another route accepts does not carry over: for example ``prefix=`` filters
``/dois`` but is ignored on ``/clients``.
"""

from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

_StrFilter = str | Sequence[str] | None
_BoolFilter = bool | None
_IntFilter = int | None
_SharedConfig = ConfigDict(extra="allow", populate_by_name=True)


class DoiFilters(BaseModel):
    """Filter model for the ``/dois`` route.

    ``state`` is ``findable``, ``registered``, or ``draft``. Without a login
    the API ignores ``registered`` and ``draft`` and answers as for
    ``findable``. ``affiliation-id`` and ``funded-by`` take ROR ids,
    ``funder-id`` a Crossref Funder ID, and ``user-id`` an ORCID iD, bare or
    as a URL. Date filters (``created``, ``registered``, ``published``) take a
    year or a comma-separated list of years. ``field-of-science`` takes the
    plain label (``natural sciences``). ``has-citations``,
    ``has-references``, ``has-parts``, ``has-part-of``, ``has-versions``,
    ``has-version-of``, ``has-views``, and ``has-downloads`` take a minimum
    count (``1``); ``true`` does not work for them, while it does for
    ``has-person``, ``has-affiliation``, ``has-organization``, and
    ``has-funder``. ``random=true`` draws random records, and
    ``sample_group="client"`` draws one random record per client account (a
    slow query, about two minutes on 2026-11-28). ``sample_size`` did not
    change the number of records on 2026-11-28; the page size decides how
    many of the drawn records come back.
    """

    model_config = _SharedConfig

    created: _StrFilter = None
    registered: _StrFilter = None
    published: _StrFilter = None
    prefix: _StrFilter = None
    provider_id: _StrFilter = Field(None, alias="provider-id")
    client_id: _StrFilter = Field(None, alias="client-id")
    consortium_id: _StrFilter = Field(None, alias="consortium-id")
    client_type: _StrFilter = Field(None, alias="client-type")
    certificate: _StrFilter = None
    state: _StrFilter = None
    source: _StrFilter = None
    schema_version: _StrFilter = Field(None, alias="schema-version")
    affiliation_id: _StrFilter = Field(None, alias="affiliation-id")
    affiliation_country: _StrFilter = Field(None, alias="affiliation-country")
    funded_by: _StrFilter = Field(None, alias="funded-by")
    include_funder_child_organizations: _BoolFilter = Field(
        None, alias="include-funder-child-organizations"
    )
    funder_id: _StrFilter = Field(None, alias="funder-id")
    user_id: _StrFilter = Field(None, alias="user-id")
    resource_type_id: _StrFilter = Field(None, alias="resource-type-id")
    resource_type: _StrFilter = None
    subject: _StrFilter = None
    field_of_science: _StrFilter = Field(None, alias="field-of-science")
    license: _StrFilter = None
    link_check_status: _StrFilter = Field(None, alias="link-check-status")
    enriched: _BoolFilter = None
    has_citations: _IntFilter = Field(None, alias="has-citations")
    has_references: _IntFilter = Field(None, alias="has-references")
    has_parts: _IntFilter = Field(None, alias="has-parts")
    has_part_of: _IntFilter = Field(None, alias="has-part-of")
    has_versions: _IntFilter = Field(None, alias="has-versions")
    has_version_of: _IntFilter = Field(None, alias="has-version-of")
    has_views: _IntFilter = Field(None, alias="has-views")
    has_downloads: _IntFilter = Field(None, alias="has-downloads")
    has_person: _BoolFilter = Field(None, alias="has-person")
    has_affiliation: _BoolFilter = Field(None, alias="has-affiliation")
    has_organization: _BoolFilter = Field(None, alias="has-organization")
    has_funder: _BoolFilter = Field(None, alias="has-funder")
    random: _BoolFilter = None
    sample_size: _IntFilter = Field(None, alias="sample-size")
    sample_group: _StrFilter = None


class ClientFilters(BaseModel):
    """Filter model for the ``/clients`` route.

    ``client-type`` is ``repository``, ``periodical``, ``igsnCatalog``, or
    ``raidRegistry``; ``repository-type`` is ``disciplinary``,
    ``governmental``, ``institutional``, ``multidisciplinary``,
    ``project-related``, or ``other``; ``year`` is the year the client was
    created; ``software`` is the repository software (``dspace``).
    """

    model_config = _SharedConfig

    year: _StrFilter = None
    client_type: _StrFilter = Field(None, alias="client-type")
    provider_id: _StrFilter = Field(None, alias="provider-id")
    certificate: _StrFilter = None
    software: _StrFilter = None
    repository_type: _StrFilter = Field(None, alias="repository-type")


class ProviderFilters(BaseModel):
    """Filter model for the ``/providers`` route.

    ``member-type`` is one of ``consortium_organization``, ``direct_member``,
    ``consortium``, ``member_only``, or ``developer`` (underscores, as in the
    payloads); ``region`` is ``emea``, ``amer``, or ``apac``, in any case.
    """

    model_config = _SharedConfig

    year: _StrFilter = None
    consortium_id: _StrFilter = Field(None, alias="consortium-id")
    member_type: _StrFilter = Field(None, alias="member-type")
    region: _StrFilter = None
    organization_type: _StrFilter = Field(None, alias="organization-type")
    focus_area: _StrFilter = None
    has_required_contacts: _BoolFilter = Field(None, alias="has-required-contacts")


class RepositoryFilters(ClientFilters):
    """Filter model for the ``/repositories`` route.

    The route serves every client account, periodicals included, and accepts
    the filters of ``/clients`` plus ``consortium-id``.
    """

    model_config = _SharedConfig

    consortium_id: _StrFilter = Field(None, alias="consortium-id")


class PrefixFilters(BaseModel):
    """Filter model for the ``/prefixes`` route.

    ``state`` is ``with-repository``, ``without-repository``, or
    ``unassigned``.
    """

    model_config = _SharedConfig

    year: _StrFilter = None
    state: _StrFilter = None
    provider_id: _StrFilter = Field(None, alias="provider-id")
    client_id: _StrFilter = Field(None, alias="client-id")


class ClientPrefixFilters(BaseModel):
    """Filter model for the ``/client-prefixes`` route."""

    model_config = _SharedConfig

    year: _StrFilter = None
    client_id: _StrFilter = Field(None, alias="client-id")
    prefix_id: _StrFilter = Field(None, alias="prefix-id")


class ProviderPrefixFilters(BaseModel):
    """Filter model for the ``/provider-prefixes`` route."""

    model_config = _SharedConfig

    year: _StrFilter = None
    consortium_id: _StrFilter = Field(None, alias="consortium-id")
    provider_id: _StrFilter = Field(None, alias="provider-id")
    prefix_id: _StrFilter = Field(None, alias="prefix-id")


class EventFilters(BaseModel):
    """Filter model for the ``/events`` route.

    ``relation-type-id`` takes DataCite relation type ids in their stored
    spelling (``references``, ``is-referenced-by``, ``cites``); ``subj-id``
    and ``obj-id`` take the full identifier URLs, ``doi`` a bare DOI that
    may appear on either side. The unfiltered collection is large and slow,
    so prefer a filter.
    """

    model_config = _SharedConfig

    subj_id: _StrFilter = Field(None, alias="subj-id")
    obj_id: _StrFilter = Field(None, alias="obj-id")
    doi: _StrFilter = None
    prefix: _StrFilter = None
    orcid: _StrFilter = None
    year_month: _StrFilter = Field(None, alias="year-month")
    source_id: _StrFilter = Field(None, alias="source-id")
    relation_type_id: _StrFilter = Field(None, alias="relation-type-id")
    subtype: _StrFilter = None
    citation_type: _StrFilter = Field(None, alias="citation-type")
    registrant_id: _StrFilter = Field(None, alias="registrant-id")
    publication_year: _StrFilter = Field(None, alias="publication-year")


def serialize_filter_params(
    filters: BaseModel | Mapping[str, Any] | None,
) -> dict[str, str]:
    """Convert filter criteria into DataCite query parameters.

    Each criterion becomes its own parameter. A sequence value joins with
    commas (DataCite reads that as ``OR``); ``None`` values are dropped.
    """
    if filters is None:
        return {}
    if isinstance(filters, BaseModel):
        dumped = filters.model_dump(exclude_none=True, by_alias=True)
    else:
        dumped = {key: value for key, value in filters.items() if value is not None}
    params: dict[str, str] = {}
    for key, value in dumped.items():
        if isinstance(value, bool):
            params[str(key)] = str(value).lower()
        elif isinstance(value, str):
            params[str(key)] = value
        elif isinstance(value, Sequence) and not isinstance(value, bytes):
            values = list(value)
            if values:
                params[str(key)] = ",".join(str(item) for item in values)
        else:
            params[str(key)] = str(value)
    return params


__all__ = [
    "ClientFilters",
    "ClientPrefixFilters",
    "DoiFilters",
    "EventFilters",
    "PrefixFilters",
    "ProviderFilters",
    "ProviderPrefixFilters",
    "RepositoryFilters",
    "serialize_filter_params",
]
