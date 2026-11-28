"""Pydantic models for ROR v2 organization records."""

from bibliofabric import SafeList, SafeStr
from pydantic import BaseModel, ConfigDict

_DISPLAY_NAME_TYPE = "ror_display"


class AdminDate(BaseModel):
    """Creation or modification date of a record and the schema version then."""

    date: str | None = None
    schema_version: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class Admin(BaseModel):
    """Record provenance: when ROR created and last modified the record."""

    created: AdminDate | None = None
    last_modified: AdminDate | None = None

    model_config = ConfigDict(extra="allow")


class ExternalId(BaseModel):
    """One external identifier scheme of an organization.

    ``type`` is ``fundref``, ``grid``, ``isni``, or ``wikidata``. ``all``
    lists every known value and ``preferred`` the one ROR displays
    (``None`` when there is a single value).
    """

    type: SafeStr | None = None
    all: SafeList[str] = []
    preferred: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class Link(BaseModel):
    """A web link of an organization (``website``, ``wikipedia``)."""

    type: SafeStr | None = None
    value: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class GeonamesDetails(BaseModel):
    """Geonames place details of a location."""

    continent_code: SafeStr | None = None
    continent_name: SafeStr | None = None
    country_code: SafeStr | None = None
    country_name: SafeStr | None = None
    country_subdivision_code: SafeStr | None = None
    country_subdivision_name: SafeStr | None = None
    lat: float | None = None
    lng: float | None = None
    name: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class Location(BaseModel):
    """A physical location of an organization."""

    geonames_id: int | None = None
    geonames_details: GeonamesDetails | None = None

    model_config = ConfigDict(extra="allow")


class Name(BaseModel):
    """An organization name.

    ``types`` holds any of ``ror_display``, ``label``, ``alias`` and
    ``acronym``. ``lang`` is ``None`` when the name has no language
    (acronyms, most aliases).
    """

    lang: str | None = None
    types: SafeList[str] = []
    value: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class Relationship(BaseModel):
    """A link to another organization.

    ``type`` is ``parent``, ``child``, ``related``, ``successor``, or
    ``predecessor``; ``id`` is the ROR URL of the other record.
    """

    id: SafeStr | None = None
    label: SafeStr | None = None
    type: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class Organization(BaseModel):
    """A ROR v2 organization record (schema 2.1).

    ``id`` is the record URL (``https://ror.org/006hf6230``), ``status`` is
    ``active``, ``inactive``, or ``withdrawn``, and ``types`` holds any of
    ``archive``, ``company``, ``education``, ``facility``, ``funder``,
    ``government``, ``healthcare``, ``nonprofit``, and ``other``.
    """

    id: SafeStr | None = None
    names: SafeList[Name] = []
    types: SafeList[str] = []
    status: SafeStr | None = None
    established: int | None = None
    domains: SafeList[str] = []
    links: SafeList[Link] = []
    locations: SafeList[Location] = []
    external_ids: SafeList[ExternalId] = []
    relationships: SafeList[Relationship] = []
    admin: Admin | None = None

    model_config = ConfigDict(extra="allow")

    @property
    def display_name(self) -> str | None:
        """The name ROR displays, else the first label, else the first name."""
        for wanted in (_DISPLAY_NAME_TYPE, "label"):
            for name in self.names:
                if wanted in name.types and name.value:
                    return name.value
        return self.names[0].value if self.names else None

    def external_ids_of_type(self, id_type: str) -> list[str]:
        """Return every ``external_ids.all`` value whose ``type`` is ``id_type``."""
        return [
            value
            for external_id in self.external_ids
            if external_id.type == id_type
            for value in external_id.all
        ]


class AffiliationMatch(BaseModel):
    """One candidate of an affiliation string match.

    ROR marks exactly one candidate ``chosen`` and scores each from 0 to 1.
    """

    substring: SafeStr | None = None
    score: float | None = None
    matching_type: SafeStr | None = None
    chosen: bool | None = None
    organization: Organization | None = None

    model_config = ConfigDict(extra="allow")


class FacetCount(BaseModel):
    """One bucket of the summary counts in ``Page.meta`` (``id``, ``title``, ``count``)."""

    id: SafeStr | None = None
    title: SafeStr | None = None
    count: int | None = None

    model_config = ConfigDict(extra="allow")
