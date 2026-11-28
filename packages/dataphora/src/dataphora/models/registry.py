"""Pydantic models for DataCite clients, providers, repositories, prefixes,
events, activities, and usage routes."""

from typing import Any

from bibliofabric import SafeList, SafeStr
from pydantic import Field

from .common import DataphoraModel, DataphoraResource


class Issn(DataphoraModel):
    """The ISSN contacts of a client or repository (``issnl``,
    ``print``, ``electronic``)."""

    issnl: SafeStr | None = None
    print: SafeList[SafeStr] = []
    electronic: SafeList[SafeStr] = []


class DataphoraClientRecord(DataphoraResource):
    """A DataCite client account: the repository or periodical that
    registers DOIs under a provider."""

    name: SafeStr | None = None
    symbol: SafeStr | None = None
    year: int | None = None
    alternateName: SafeList[SafeStr] = []
    description: SafeStr | None = None
    language: SafeList[SafeStr] = []
    clientType: SafeStr | None = None
    domains: SafeList[SafeStr] = []
    re3data: SafeStr | None = None
    opendoar: SafeStr | None = None
    issn: Issn | None = None
    url: SafeStr | None = None
    created: SafeStr | None = None
    updated: SafeStr | None = None
    isActive: bool | None = None


class DataphoraProvider(DataphoraResource):
    """A DataCite provider: the member or consortium organization that
    manages clients and prefixes."""

    name: SafeStr | None = None
    displayName: SafeStr | None = None
    symbol: SafeStr | None = None
    website: SafeStr | None = None
    description: SafeStr | None = None
    region: SafeStr | None = None
    country: SafeStr | None = None
    logoUrl: SafeStr | None = None
    memberType: SafeStr | None = None
    organizationType: SafeStr | None = None
    focusArea: SafeStr | None = None
    nonProfitStatus: SafeStr | None = None
    isActive: bool | None = None
    joined: SafeStr | None = None
    rorId: SafeStr | None = None
    created: SafeStr | None = None
    updated: SafeStr | None = None
    doiEstimate: int | None = None


class DataphoraRepository(DataphoraResource):
    """A DataCite repository: the re3data/OpenDOAR view of a client."""

    name: SafeStr | None = None
    symbol: SafeStr | None = None
    re3data: SafeStr | None = None
    opendoar: SafeStr | None = None
    year: int | None = None
    alternateName: SafeList[SafeStr] = []
    description: SafeStr | None = None
    clientType: SafeStr | None = None
    repositoryType: SafeList[SafeStr] = []
    language: SafeList[SafeStr] = []
    certificate: SafeList[SafeStr] = []
    domains: SafeList[SafeStr] = []
    issn: Issn | None = None
    url: SafeStr | None = None
    software: SafeStr | None = None
    subjects: SafeList[SafeStr] = []
    created: SafeStr | None = None
    updated: SafeStr | None = None
    isActive: bool | None = None


class DataphoraPrefix(DataphoraResource):
    """A DataCite DOI prefix (``10.5438``).

    ``id`` and ``prefix`` are the same string; ``createdAt`` is the only
    other attribute the API returns.
    """

    prefix: SafeStr | None = None
    createdAt: SafeStr | None = None


class DataphoraEvent(DataphoraResource):
    """A DataCite event: one relation between two identifiers.

    Attribute keys are hyphenated upstream; the fields here carry aliases
    so both spellings validate. ``subj-id`` and ``obj-id`` name the two
    ends, ``relation-type-id`` the relation (``references``, ``cites``,
    ``is-cited-by``); the ``subj`` and ``obj`` relationships hold the
    identifier pairs. ``occured-at`` keeps the upstream spelling, which
    misses an ``r``.
    """

    subj_id: SafeStr | None = Field(None, alias="subj-id")
    obj_id: SafeStr | None = Field(None, alias="obj-id")
    source_id: SafeStr | None = Field(None, alias="source-id")
    relation_type_id: SafeStr | None = Field(None, alias="relation-type-id")
    total: int | None = None
    message_action: SafeStr | None = Field(None, alias="message-action")
    source_token: SafeStr | None = Field(None, alias="source-token")
    license: SafeStr | None = None
    occured_at: SafeStr | None = Field(None, alias="occured-at")
    occurred_at: SafeStr | None = Field(None, alias="occurred-at")
    timestamp: SafeStr | None = None


class DataphoraActivity(DataphoraResource):
    """One provenance activity in a DOI's history (``action``,
    ``version``, ``changes``).

    The ``prov:*`` attribute keys carry the provenance links and land in
    ``model_extra``. ``changes`` maps each changed attribute to its
    ``[old, new]`` pair.
    """

    action: SafeStr | None = None
    version: int | None = None
    changes: dict[str, Any] | None = None
    requestId: SafeStr | None = None


class FacetCount(DataphoraModel):
    """One bucket of a facet or statistics list (``id``, ``title``, ``count``)."""

    id: str
    title: SafeStr | None = None
    count: int | None = None


class DataphoraTotals(DataphoraModel):
    """One entry of a ``/totals`` statistics route.

    ``temporal`` groups counts by ``this_month``, ``this_year``,
    ``last_year``, and ``two_years_ago``; ``states`` breaks the count down
    by DOI state. The body of these routes is a bare array, not a JSON:API
    envelope.
    """

    id: str
    title: SafeStr | None = None
    count: int | None = None
    temporal: dict[str, list[FacetCount]] | None = None
    states: list[FacetCount] | None = None


class DataphoraClientPrefix(DataphoraResource):
    """The assignment of one DOI prefix to one client account.

    The prefix and the account are relationships (``prefix``, ``client``);
    the resource itself only carries timestamps.
    """

    createdAt: SafeStr | None = None
    updatedAt: SafeStr | None = None


class DataphoraProviderPrefix(DataphoraResource):
    """The assignment of one DOI prefix to one provider.

    The prefix and the provider are relationships (``prefix``,
    ``provider``); the resource itself only carries timestamps.
    """

    createdAt: SafeStr | None = None
    updatedAt: SafeStr | None = None


__all__ = [
    "FacetCount",
    "DataphoraActivity",
    "DataphoraClientRecord",
    "DataphoraClientPrefix",
    "DataphoraEvent",
    "DataphoraPrefix",
    "DataphoraProvider",
    "DataphoraProviderPrefix",
    "DataphoraRepository",
    "DataphoraTotals",
]
