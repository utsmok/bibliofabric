"""Pydantic models for DataCite DOI records.

Field names follow the JSON attributes of the live API (verified
2026-11-27). Without the ``detail=true`` or ``affiliation=true``/``publisher=true``
request flags some attributes are trimmed or omitted upstream; those fields
are optional here and extras are always kept.
"""

from bibliofabric import SafeList, SafeStr
from pydantic import ConfigDict, model_validator

from .common import DataphoraModel, DataphoraResource

_PersonConfig = ConfigDict(extra="allow", populate_by_name=True)


class NameIdentifier(DataphoraModel):
    """One persistent identifier of a person (ORCID, ROR, and similar)."""

    nameIdentifier: SafeStr | None = None
    nameIdentifierScheme: SafeStr | None = None
    schemeUri: SafeStr | None = None


class Affiliation(DataphoraModel):
    """An affiliation of a creator or contributor.

    DataCite omits ``affiliationIdentifier`` fields from responses unless
    the request carries ``affiliation=true``, and older records carry bare
    strings, which this model wraps as ``name``.
    """

    name: SafeStr | None = None
    affiliationIdentifier: SafeStr | None = None
    affiliationIdentifierScheme: SafeStr | None = None
    schemeUri: SafeStr | None = None
    lang: SafeStr | None = None

    @model_validator(mode="before")
    @classmethod
    def _wrap_bare_string(cls, value: object) -> object:
        """Wrap a bare affiliation string as ``name``."""
        if isinstance(value, str):
            return {"name": value}
        return value


class Creator(DataphoraModel):
    """One creator of a DOI (or contributor, minus ``contributorType``)."""

    name: SafeStr | None = None
    nameType: SafeStr | None = None
    givenName: SafeStr | None = None
    familyName: SafeStr | None = None
    lang: SafeStr | None = None
    nameIdentifiers: SafeList[NameIdentifier] = []
    affiliation: SafeList[Affiliation] = []


class Contributor(Creator):
    """One contributor of a DOI; ``contributorType`` names the role."""

    contributorType: SafeStr | None = None


class Title(DataphoraModel):
    """One title of a DOI; ``titleType`` marks translated or alternative titles."""

    title: SafeStr | None = None
    titleType: SafeStr | None = None
    lang: SafeStr | None = None


class Subject(DataphoraModel):
    """One subject, keyword, or classification of a DOI."""

    subject: SafeStr | None = None
    subjectScheme: SafeStr | None = None
    schemeUri: SafeStr | None = None
    valueUri: SafeStr | None = None
    classificationCode: SafeStr | None = None
    lang: SafeStr | None = None


class Date(DataphoraModel):
    """One date of a DOI with its ``dateType`` (``Issued``, ``Created``)."""

    date: SafeStr | None = None
    dateType: SafeStr | None = None
    dateInformation: SafeStr | None = None


class Types(DataphoraModel):
    """The resource types of a DOI in several metadata schemes."""

    resourceTypeGeneral: SafeStr | None = None
    resourceType: SafeStr | None = None
    bibtex: SafeStr | None = None
    citeproc: SafeStr | None = None
    schemaOrg: SafeStr | None = None


class Publisher(DataphoraModel):
    """The publisher of a DOI.

    Schema 4.5 makes this an object; DataCite omits
    ``publisherIdentifier`` fields unless the request carries
    ``publisher=true``.
    """

    name: SafeStr | None = None
    publisherIdentifier: SafeStr | None = None
    schemeUri: SafeStr | None = None
    lang: SafeStr | None = None


class Identifier(DataphoraModel):
    """One alternate identifier of a DOI (added by ``detail=true``)."""

    identifier: SafeStr | None = None
    identifierType: SafeStr | None = None


class RelatedIdentifier(DataphoraModel):
    """One related identifier of a DOI with its relation type."""

    relatedIdentifier: SafeStr | None = None
    relatedIdentifierType: SafeStr | None = None
    relationType: SafeStr | None = None
    resourceTypeGeneral: SafeStr | None = None
    relatedMetadataScheme: SafeStr | None = None
    schemeUri: SafeStr | None = None
    schemeType: SafeStr | None = None


class RelatedItemIdentifier(DataphoraModel):
    """The identifier of a related item."""

    relatedItemIdentifier: SafeStr | None = None
    relatedItemIdentifierType: SafeStr | None = None


class RelatedItem(DataphoraModel):
    """One related item (a journal issue, book chapter) of a DOI."""

    relatedItemIdentifier: RelatedItemIdentifier | None = None
    relatedItemType: SafeStr | None = None
    relationType: SafeStr | None = None
    creators: SafeList[Creator] = []
    titles: SafeList[Title] = []
    volume: SafeStr | None = None
    issue: SafeStr | None = None
    number: SafeStr | None = None
    firstPage: SafeStr | None = None
    lastPage: SafeStr | None = None
    publisher: Publisher | None = None
    publicationYear: int | None = None
    edition: SafeStr | None = None
    contributors: SafeList[Contributor] = []
    subjects: SafeList[Subject] = []


class Rights(DataphoraModel):
    """One license or rights statement of a DOI."""

    rights: SafeStr | None = None
    rightsUri: SafeStr | None = None
    schemeUri: SafeStr | None = None
    rightsIdentifier: SafeStr | None = None
    rightsIdentifierScheme: SafeStr | None = None
    lang: SafeStr | None = None


class Description(DataphoraModel):
    """One description (abstract, methods) of a DOI."""

    description: SafeStr | None = None
    descriptionType: SafeStr | None = None
    lang: SafeStr | None = None


class GeoPoint(DataphoraModel):
    """One geographic point (``pointLongitude``, ``pointLatitude``)."""

    pointLongitude: SafeStr | None = None
    pointLatitude: SafeStr | None = None


class GeoLocationBox(DataphoraModel):
    """One bounding box (``westBoundLongitude`` and friends)."""

    westBoundLongitude: SafeStr | None = None
    eastBoundLongitude: SafeStr | None = None
    southBoundLatitude: SafeStr | None = None
    northBoundLatitude: SafeStr | None = None


class GeoLocation(DataphoraModel):
    """One geographic location of a DOI."""

    geoLocationPlace: SafeStr | None = None
    geoLocationPoint: GeoPoint | None = None
    geoLocationBox: GeoLocationBox | None = None


class FundingReference(DataphoraModel):
    """One funding source of a DOI."""

    funderName: SafeStr | None = None
    funderIdentifier: SafeStr | None = None
    funderIdentifierType: SafeStr | None = None
    awardNumber: SafeStr | None = None
    awardUri: SafeStr | None = None
    awardTitle: SafeStr | None = None


class Container(DataphoraModel):
    """The larger work a DOI appeared in (journal, volume)."""

    type: SafeStr | None = None
    identifier: SafeStr | None = None
    identifierType: SafeStr | None = None
    title: SafeStr | None = None
    volume: SafeStr | None = None
    issue: SafeStr | None = None
    firstPage: SafeStr | None = None
    lastPage: SafeStr | None = None


class OverTime(DataphoraModel):
    """One bucket of a ``viewsOverTime`` or ``citationsOverTime`` series."""

    yearMonth: SafeStr | None = None
    total: int | None = None


class DataphoraDoi(DataphoraResource):
    """A DataCite DOI record.

    ``id`` and ``doi`` are the same DOI string. ``state`` is ``findable``,
    ``registered``, or ``draft``; anonymous reads only see ``findable``
    records. The usage counters (``viewCount``, ``downloadCount``,
    ``citationCount``, and friends) arrive with every record, while the
    ``xml`` metadata and the ``*OverTime`` series only arrive with
    ``detail=true``.
    """

    doi: SafeStr | None = None
    identifiers: SafeList[Identifier] = []
    creators: SafeList[Creator] = []
    titles: SafeList[Title] = []
    publisher: Publisher | str | None = None
    container: Container | None = None
    publicationYear: int | None = None
    subjects: SafeList[Subject] = []
    contributors: SafeList[Contributor] = []
    dates: SafeList[Date] = []
    language: SafeStr | None = None
    types: Types | None = None
    relatedIdentifiers: SafeList[RelatedIdentifier] = []
    relatedItems: SafeList[RelatedItem] = []
    sizes: SafeList[SafeStr] = []
    formats: SafeList[SafeStr] = []
    version: SafeStr | None = None
    rightsList: SafeList[Rights] = []
    descriptions: SafeList[Description] = []
    geoLocations: SafeList[GeoLocation] = []
    fundingReferences: SafeList[FundingReference] = []
    url: SafeStr | None = None
    contentUrl: SafeList[SafeStr] = []
    metadataVersion: int | str | None = None
    schemaVersion: SafeStr | None = None
    source: SafeStr | None = None
    isActive: bool | None = None
    state: SafeStr | None = None
    reason: SafeStr | None = None
    viewCount: int | None = None
    downloadCount: int | None = None
    referenceCount: int | None = None
    citationCount: int | None = None
    partCount: int | None = None
    partOfCount: int | None = None
    versionCount: int | None = None
    versionOfCount: int | None = None
    created: SafeStr | None = None
    registered: SafeStr | None = None
    published: int | str | None = None
    updated: SafeStr | None = None
    xml: SafeStr | None = None
    prefix: SafeStr | None = None
    suffix: SafeStr | None = None
    viewsOverTime: SafeList[OverTime] = []
    citationsOverTime: SafeList[OverTime] = []
    alternateIdentifiers: SafeList[Identifier] = []

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    @property
    def title(self) -> str | None:
        """The first title text, ``None`` when the record has no titles."""
        for entry in self.titles:
            if entry.title is not None:
                return entry.title
        return None

    @property
    def resource_type(self) -> str | None:
        """The ``resourceTypeGeneral`` value (``dataset``, ``text``)."""
        return self.types.resourceTypeGeneral if self.types else None

    @property
    def client_id(self) -> str | None:
        """The repository (client) account that registered the DOI."""
        relationship = (self.relationships or {}).get("client")
        if (
            relationship is None
            or relationship.data is None
            or isinstance(relationship.data, list)
        ):
            return None
        return relationship.data.id

    @property
    def provider_id(self) -> str | None:
        """The DataCite provider (member) behind the registering client."""
        relationship = (self.relationships or {}).get("provider")
        if (
            relationship is None
            or relationship.data is None
            or isinstance(relationship.data, list)
        ):
            return None
        return relationship.data.id


__all__ = [
    "Affiliation",
    "Container",
    "Contributor",
    "Creator",
    "Date",
    "Description",
    "FundingReference",
    "GeoLocation",
    "GeoLocationBox",
    "GeoPoint",
    "Identifier",
    "NameIdentifier",
    "OverTime",
    "Publisher",
    "RelatedIdentifier",
    "RelatedItem",
    "RelatedItemIdentifier",
    "Rights",
    "Subject",
    "Title",
    "DataphoraDoi",
    "Types",
]
