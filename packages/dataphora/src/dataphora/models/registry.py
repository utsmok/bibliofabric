"""Pydantic models for DataCite clients, providers, repositories, prefixes,
events, activities, and usage routes."""

from typing import Annotated, Any

from bibliofabric import SafeList, SafeStr
from pydantic import BeforeValidator, Field

from .common import DataphoraModel, DataphoraResource
from .doi import Subject


class Issn(DataphoraModel):
    """The ISSN contacts of a client or repository (``issnl``,
    ``print``, ``electronic``)."""

    issnl: SafeStr | None = None
    print: SafeList[SafeStr] = []
    electronic: SafeList[SafeStr] = []


def _empty_issn_to_none(value: object) -> object:
    """Read the empty list upstream sends for accounts without an ISSN as
    ``None``."""
    return None if isinstance(value, list) and not value else value


OptionalIssn = Annotated[Issn | None, BeforeValidator(_empty_issn_to_none)]


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
    issn: OptionalIssn = None
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
    issn: OptionalIssn = None
    url: SafeStr | None = None
    software: SafeStr | None = None
    subjects: SafeList[Subject] = []
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
    identifier pairs, and ``occurred-at`` the event time.
    """

    subj_id: SafeStr | None = Field(None, alias="subj-id")
    obj_id: SafeStr | None = Field(None, alias="obj-id")
    source_id: SafeStr | None = Field(None, alias="source-id")
    relation_type_id: SafeStr | None = Field(None, alias="relation-type-id")
    total: int | None = None
    message_action: SafeStr | None = Field(None, alias="message-action")
    source_token: SafeStr | None = Field(None, alias="source-token")
    license: SafeStr | None = None
    occurred_at: SafeStr | None = Field(None, alias="occurred-at")
    timestamp: SafeStr | None = None


class DataphoraActivity(DataphoraResource):
    """One provenance activity in the history of a DOI or an account.

    The ``prov_*`` fields carry the ``prov:`` attributes upstream: which
    activity ran, when, which DOI or account it changed, and which account
    made the change. ``changes`` maps each changed attribute to its
    ``[old, new]`` pair.
    """

    prov_was_generated_by: SafeStr | None = Field(None, alias="prov:wasGeneratedBy")
    prov_generated_at_time: SafeStr | None = Field(None, alias="prov:generatedAtTime")
    prov_was_derived_from: SafeStr | None = Field(None, alias="prov:wasDerivedFrom")
    prov_was_attributed_to: SafeStr | None = Field(None, alias="prov:wasAttributedTo")
    action: SafeStr | None = None
    version: int | None = None
    changes: dict[str, Any] | None = None


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
