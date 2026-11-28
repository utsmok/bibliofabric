"""Pydantic filter models for the DataCite REST API.

Each field maps to one query parameter of the ``/dois`` route (verified
against the live API and the DataCite documentation on 2026-11-27). A value
that is a sequence joins its items with a comma, which DataCite reads as
``OR``; different keys ``AND``. Every model allows extra fields, so filters
added upstream stay usable before they land here.

The API silently ignores unknown query parameters, so a misspelled filter
changes nothing instead of failing; prefer the typed fields.
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

    ``state`` is ``findable``, ``registered``, or ``draft``; anonymous reads
    only ever see ``findable`` records, so ``registered`` and ``draft`` need
    a login. ``affiliation-id``, ``funded-by``, and ``user-id`` take ROR ids
    and ORCID iDs either bare or as URLs. Date filters (``created``,
    ``registered``, ``published``) take a year or a comma-separated list of
    years.
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
    sample_size: _IntFilter = None
    sample_group: _StrFilter = None


class ClientFilters(BaseModel):
    """Filter model for the ``/clients`` route.

    ``client-type`` is ``repository`` or ``periodical``; ``year`` takes a
    year or a comma-separated list of years. The remaining keys mirror the
    filters of the ``/dois`` route with the same meaning.
    """

    model_config = _SharedConfig

    year: _StrFilter = None
    client_type: _StrFilter = Field(None, alias="client-type")
    provider_id: _StrFilter = Field(None, alias="provider-id")
    consortium_id: _StrFilter = Field(None, alias="consortium-id")
    prefix: _StrFilter = None
    certificate: _StrFilter = None
    repositories: _BoolFilter = None
    created: _StrFilter = None
    registered: _StrFilter = None
    published: _StrFilter = None
    resource_type_id: _StrFilter = Field(None, alias="resource-type-id")
    resource_type: _StrFilter = None
    subject: _StrFilter = None
    field_of_science: _StrFilter = Field(None, alias="field-of-science")
    license: _StrFilter = None
    affiliation_id: _StrFilter = Field(None, alias="affiliation-id")
    funded_by: _StrFilter = Field(None, alias="funded-by")


class ProviderFilters(BaseModel):
    """Filter model for the ``/providers`` route.

    ``member-type`` is one of ``direct-member``, ``consortium``,
    ``consortium-organization``, ``for-profit-provider``,
    ``provider``, or ``epoch-member``; ``region`` is one of ``amer``,
    ``apa``, ``emea``.
    """

    model_config = _SharedConfig

    year: _StrFilter = None
    member_type: _StrFilter = Field(None, alias="member-type")
    region: _StrFilter = None
    organization_type: _StrFilter = Field(None, alias="organization-type")
    focus_area: _StrFilter = None
    non_profit_status: _StrFilter = Field(None, alias="non-profit-status")
    country: _StrFilter = None


class RepositoryFilters(BaseModel):
    """Filter model for the ``/repositories`` route.

    ``repository-type`` values are free text (``governmental``,
    ``institutional``, and similar); ``certificate`` takes repository
    certificate names such as ``CoreTrustSeal``.
    """

    model_config = _SharedConfig

    year: _StrFilter = None
    repository_type: _StrFilter = Field(None, alias="repository-type")
    certificate: _StrFilter = None
    provider_id: _StrFilter = Field(None, alias="provider-id")
    consortium_id: _StrFilter = Field(None, alias="consortium-id")
    software: _StrFilter = None
    prefix: _StrFilter = None
    client_type: _StrFilter = Field(None, alias="client-type")


class PrefixFilters(BaseModel):
    """Filter model for the ``/prefixes`` route."""

    model_config = _SharedConfig

    year: _StrFilter = None
    state: _StrFilter = None
    provider_id: _StrFilter = Field(None, alias="provider-id")
    client_id: _StrFilter = Field(None, alias="client-id")
    consortium_id: _StrFilter = Field(None, alias="consortium-id")


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
    "DoiFilters",
    "EventFilters",
    "PrefixFilters",
    "ProviderFilters",
    "RepositoryFilters",
    "serialize_filter_params",
]
