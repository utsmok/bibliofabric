# aireloom/models/research_product.py
"""Pydantic models for representing OpenAIRE Research Product entities.

This module defines the Pydantic model for an OpenAIRE Research Product,
which can be a publication, dataset, software, or other research output.
It includes nested models for authors, persistent identifiers (PIDs), access
rights, citation impacts, instances, related records, and typed relationship
lists, matching the current Graph API V3/V4 response shape (1.6.0).
Reference: https://graph.openaire.eu/docs/data-model/entities/research-product
"""

from typing import Annotated, Literal

from bibliofabric import SafeList, SafeStr
from pydantic import (
    AliasChoices,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    computed_field,
)

from .._helpers import extract_all_pids_by_scheme, extract_pid_by_scheme
from .base import (
    BaseEntity,
    CfHbKeyValue,
    CodeLabel,
    DsRef,
    FundingHierarchy,
    Pid,
    Provenance,
    RelatedRecordHeader,
    SafeCfHbKeyValue,
    SafeCodeLabel,
    SafeDsRef,
    SafeFundingHierarchy,
    SafeRelatedRecordHeader,
    TypedPid,
)

OpenAccessRouteType = Literal["gold", "green", "hybrid", "bronze"]
"""Type alias for allowed Open Access routes (e.g., gold, green)."""

RefereedType = str
"""Type alias for refereed status (known values include ``peerReviewed``, ``nonPeerReviewed``, ``UNKNOWN``)."""

ResearchProductType = Literal["publication", "dataset", "software", "other"]
"""Type alias for the type of research product (e.g., publication, dataset)."""


class AuthorPid(BaseModel):
    """Author PID payload: ``{"id": {scheme, value}, "provenance"}``."""

    id: Pid | None = None
    provenance: Provenance | None = None

    model_config = ConfigDict(extra="allow")


class Author(BaseModel):
    """Represents an author of a research product."""

    id: str | None = None
    fullName: SafeStr = ""
    rank: int | None = None
    name: SafeStr = ""
    surname: SafeStr = ""
    pid: AuthorPid | None = None

    model_config = ConfigDict(extra="allow")


class BestAccessRight(BaseModel):
    """The best determined access right for a research product."""

    code: SafeStr = ""
    label: SafeStr = ""
    scheme: SafeStr = ""

    model_config = ConfigDict(extra="allow")


SafeBestAccessRight = Annotated[
    BestAccessRight, BeforeValidator(lambda v: BestAccessRight() if v is None else v)
]


class CitationImpact(BaseModel):
    """Citation-based impact metrics (BIP indicators).

    Known ``*Class`` values include ``C1``, ``C2``, ``C3``, ``C4``, and ``C5``.
    """

    influence: float | None = None
    influenceClass: str | None = None
    citationCount: int | None = None
    citationClass: str | None = None
    popularity: float | None = None
    popularityClass: str | None = None
    impulse: float | None = None
    impulseClass: str | None = None

    model_config = ConfigDict(extra="allow")


SafeCitationImpact = Annotated[
    CitationImpact, BeforeValidator(lambda v: CitationImpact() if v is None else v)
]


class UsageCounts(BaseModel):
    """Usage counts for a research product (downloads and views)."""

    downloads: int | None = None
    views: int | None = None

    model_config = ConfigDict(extra="allow")


SafeUsageCounts = Annotated[
    UsageCounts, BeforeValidator(lambda v: UsageCounts() if v is None else v)
]


class Indicator(BaseModel):
    """Container for the impact indicators of a research product."""

    citationImpact: SafeCitationImpact = Field(default_factory=CitationImpact)
    usageCounts: SafeUsageCounts = Field(default_factory=UsageCounts)

    model_config = ConfigDict(extra="allow")


SafeIndicator = Annotated[
    Indicator, BeforeValidator(lambda v: Indicator() if v is None else v)
]


class AccessRight(BaseModel):
    """Access rights attached to an instance of a research product."""

    code: SafeStr = ""
    label: SafeStr = ""
    openAccessRoute: OpenAccessRouteType | None = None
    scheme: SafeStr = ""

    model_config = ConfigDict(extra="allow")


SafeAccessRight = Annotated[
    AccessRight, BeforeValidator(lambda v: AccessRight() if v is None else v)
]


class ArticleProcessingCharge(BaseModel):
    """Article Processing Charge (APC) information."""

    amount: str | None = None
    currency: SafeStr = ""

    model_config = ConfigDict(extra="allow")


class Instance(BaseModel):
    """A specific instance or manifestation of a research product."""

    pids: SafeList[Pid] = Field(default_factory=list)
    alternateIdentifiers: SafeList[Pid] = Field(default_factory=list)
    license: str | None = None
    accessRight: SafeAccessRight = Field(default_factory=AccessRight)
    type: SafeStr = ""
    urls: SafeList[str] = Field(default_factory=list)
    articleProcessingCharge: ArticleProcessingCharge | None = None
    publicationDate: str | None = None
    refereed: RefereedType | None = None
    hostedBy: SafeCfHbKeyValue = Field(default_factory=CfHbKeyValue)
    collectedFrom: SafeCfHbKeyValue = Field(default_factory=CfHbKeyValue)
    distributionLocation: str | None = None
    instanceId: str | None = None
    embargoEndDate: str | None = None

    model_config = ConfigDict(extra="allow")


class Language(BaseModel):
    """A language associated with a research product."""

    code: SafeStr = ""
    label: SafeStr = ""

    model_config = ConfigDict(extra="allow")


SafeLanguage = Annotated[
    Language, BeforeValidator(lambda v: Language() if v is None else v)
]


class Subject(BaseModel):
    """A subject classification: ``{"subject": {scheme, value}, "provenance"}``."""

    subject: Pid | None = None
    provenance: Provenance | None = None

    model_config = ConfigDict(extra="allow")


class Container(BaseModel):
    """The container of a publication (journal, book series, conference)."""

    edition: str | None = None
    iss: str | None = None
    issnLinking: str | None = None
    issnOnline: str | None = None
    issnPrinted: str | None = None
    name: SafeStr = ""
    sp: str | None = None
    ep: str | None = None
    vol: str | None = None
    conferencePlace: str | None = None
    conferenceDate: str | None = None

    model_config = ConfigDict(extra="allow")


SafeContainer = Annotated[
    Container, BeforeValidator(lambda v: Container() if v is None else v)
]


class GeoLocation(BaseModel):
    """Geolocation information, typically for datasets."""

    point: str | None = None
    box: str | None = None
    place: str | None = None

    model_config = ConfigDict(extra="allow")


class EoscIfGuideline(BaseModel):
    """An EOSC IF guideline code."""

    code: SafeStr = ""

    model_config = ConfigDict(extra="allow")


class DeclaredAffiliation(BaseModel):
    """ROR/OpenOrg identifiers for a person's declared affiliation."""

    rorId: str | None = None
    openOrgId: str | None = None

    model_config = ConfigDict(extra="allow")


class RelatedInstance(BaseModel):
    """An instance embedded in ``RelatedRecord.instances``.

    OpenAIRE's OpenAPI schema uses lowercase keys here (``accessright``,
    ``instancetype``, ``url``, ``hostedby``, ``collectedfrom``, ``pid``,
    ``dateofacceptance``); camelCase aliases are also accepted for tolerance.
    """

    license: str | None = None
    accessright: SafeAccessRight = Field(
        default_factory=AccessRight,
        validation_alias=AliasChoices("accessright", "accessRight"),
    )
    instancetype: SafeStr = Field(
        default="",
        validation_alias=AliasChoices("instancetype", "type"),
    )
    hostedby: SafeDsRef = Field(
        default_factory=DsRef,
        validation_alias=AliasChoices("hostedby", "hostedBy"),
    )
    url: SafeList[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("url", "urls"),
    )
    distributionlocation: str | None = Field(
        default=None,
        validation_alias=AliasChoices("distributionlocation", "distributionLocation"),
    )
    collectedfrom: SafeDsRef = Field(
        default_factory=DsRef,
        validation_alias=AliasChoices("collectedfrom", "collectedFrom"),
    )
    pid: SafeList[TypedPid] = Field(
        default_factory=list,
        validation_alias=AliasChoices("pid", "pids"),
    )
    alternateIdentifier: SafeList[TypedPid] = Field(
        default_factory=list,
        validation_alias=AliasChoices("alternateIdentifier", "alternateIdentifiers"),
    )
    dateofacceptance: str | None = Field(
        default=None,
        validation_alias=AliasChoices("dateofacceptance", "publicationDate"),
    )
    processingcharges: ArticleProcessingCharge | None = Field(
        default=None,
        validation_alias=AliasChoices("processingcharges", "articleProcessingCharge"),
    )
    refereed: RefereedType | None = None
    fulltext: str | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class RelatedRecord(BaseModel):
    """An entry in ``links[]``: a related entity in the graph.

    The inline fields vary with ``header.relatedRecordType`` (project, result,
    organization, datasource, person); the union from the OpenAPI spec is
    declared below and unrecognised inline fields stay in ``model_extra``.
    """

    header: SafeRelatedRecordHeader = Field(default_factory=RelatedRecordHeader)
    title: SafeStr = ""
    websiteurl: str | None = None
    pid: SafeList[Pid] = Field(default_factory=list)
    collectedfrom: SafeList[DsRef] = Field(default_factory=list)
    author: SafeList[str] = Field(default_factory=list)
    description: SafeStr = ""
    dateofacceptance: str | None = None
    publisher: SafeStr = ""
    codeRepositoryUrl: str | None = None
    resulttype: str | None = None
    instances: SafeList[RelatedInstance] = Field(default_factory=list)
    officialname: SafeStr = ""
    datasourcetype: SafeCodeLabel = Field(default_factory=CodeLabel)
    datasourcetypeui: SafeCodeLabel = Field(default_factory=CodeLabel)
    openairecompatibility: SafeCodeLabel = Field(default_factory=CodeLabel)
    legalname: SafeStr = ""
    legalshortname: SafeStr = ""
    country: SafeCodeLabel = Field(default_factory=CodeLabel)
    projectTitle: str | None = None
    code: str | None = None
    acronym: str | None = None
    contracttype: SafeCodeLabel = Field(default_factory=CodeLabel)
    funding: SafeFundingHierarchy = Field(default_factory=FundingHierarchy)
    validationDate: str | None = None
    startDate: str | None = None
    endDate: str | None = None
    givenName: SafeStr = ""
    familyName: SafeStr = ""
    personRoleInProject: str | None = None
    declaredAffiliation: SafeList[DeclaredAffiliation] = Field(default_factory=list)
    affiliationsTimeline: SafeList[CodeLabel] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


class ProductProject(BaseModel):
    """A related project in ``ResearchProduct.projects``."""

    id: SafeStr = ""
    code: str | None = None
    acronym: str | None = None
    title: SafeStr = ""
    funder: str | None = None
    pids: SafeList[Pid] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


class ProductOrganization(BaseModel):
    """A related organization in ``ResearchProduct.organizations`` (1.5.0 shape)."""

    legalName: SafeStr = ""
    acronym: SafeStr = ""
    id: str | None = None
    pids: SafeList[Pid] = Field(default_factory=list)
    countries: SafeList[CodeLabel] = Field(default_factory=list)
    websiteurl: str | None = None

    model_config = ConfigDict(extra="allow")


class ProductCommunity(BaseModel):
    """A related community in ``ResearchProduct.communities``."""

    code: SafeStr = ""
    label: SafeStr = ""
    provenance: Provenance | None = None

    model_config = ConfigDict(extra="allow")


class ResearchProduct(BaseEntity):
    """Model representing an OpenAIRE Research Product entity.

    Covers the V3/V4 response surface (47 keys observed live): titles, authors,
    access rights, countries, subjects, indicators, instances, Open Access
    flags, subtype-specific fields, and typed relationship lists. Inherits
    ``id`` from ``BaseEntity``.
    """

    originalIds: SafeList[str] = Field(default_factory=list)
    pids: SafeList[Pid] = Field(default_factory=list)
    type: ResearchProductType | None = None
    mainTitle: SafeStr = ""
    subTitle: SafeStr = ""
    otherTitles: SafeList[str] = Field(default_factory=list)
    authors: SafeList[Author] = Field(default_factory=list)
    bestAccessRight: SafeBestAccessRight = Field(default_factory=BestAccessRight)
    countries: SafeList[CodeLabel] = Field(default_factory=list)
    descriptions: SafeList[str] = Field(default_factory=list)
    publicationDate: str | None = None
    publisher: SafeStr = ""
    embargoEndDate: str | None = None
    contributors: SafeList[str] = Field(default_factory=list)
    sources: SafeList[str] = Field(default_factory=list)
    formats: SafeList[str] = Field(default_factory=list)
    coverages: SafeList[str] = Field(default_factory=list)
    dateOfCollection: str | None = None
    lastUpdateTimeStamp: int | None = None
    indicators: SafeIndicator = Field(default_factory=Indicator)
    instances: SafeList[Instance] = Field(default_factory=list)
    language: SafeLanguage = Field(default_factory=Language)
    subjects: SafeList[Subject] = Field(default_factory=list)
    container: SafeContainer = Field(default_factory=Container)
    geoLocations: SafeList[GeoLocation] = Field(default_factory=list)

    # Open Access fields
    isGreen: bool | None = None
    green: bool | None = None
    isInDiamondJournal: bool | None = None
    inDiamondJournal: bool | None = None
    openAccessColor: str | None = None
    publiclyFunded: bool | None = None
    eoscIfGuidelines: SafeList[EoscIfGuideline] = Field(default_factory=list)

    # Subtype-specific fields (Software)
    codeRepositoryUrl: str | None = None
    documentationUrls: SafeList[str] = Field(default_factory=list)
    programmingLanguage: str | None = None

    # Subtype-specific fields (Dataset)
    size: str | None = None
    version: str | None = None

    # Subtype-specific fields (Other)
    contactPeople: SafeList[str] = Field(default_factory=list)
    contactGroups: SafeList[str] = Field(default_factory=list)
    tools: SafeList[str] = Field(default_factory=list)

    # Relationship fields
    collectedFrom: SafeList[CfHbKeyValue] = Field(default_factory=list)
    projects: SafeList[ProductProject] = Field(default_factory=list)
    organizations: SafeList[ProductOrganization] = Field(default_factory=list)
    communities: SafeList[ProductCommunity] = Field(default_factory=list)
    links: SafeList[RelatedRecord] = Field(default_factory=list)

    # ── Computed fields ─────────────────────────────────────────────────

    @computed_field
    @property
    def doi(self) -> str | None:
        """First DOI from the pids list."""
        return extract_pid_by_scheme(self.pids, "doi")

    @computed_field
    @property
    def all_dois(self) -> list[str]:
        """All DOI values from the pids list."""
        return extract_all_pids_by_scheme(self.pids, "doi")

    @computed_field
    @property
    def is_open_access(self) -> bool:
        """True when the best access right is OPEN."""
        return self.bestAccessRight.label.upper() == "OPEN"

    @computed_field
    @property
    def open_access_url(self) -> str | None:
        """URL of the first instance whose access right is OPEN."""
        for inst in self.instances:
            if (
                inst.accessRight
                and inst.accessRight.label
                and inst.accessRight.label.upper() == "OPEN"
                and inst.urls
            ):
                return inst.urls[0]
        return None

    @computed_field
    @property
    def citation_count(self) -> int | None:
        """Citation count from indicators, if available."""
        return self.indicators.citationImpact.citationCount

    @computed_field
    @property
    def publication_year(self) -> int | None:
        """Year parsed from publicationDate."""
        if self.publicationDate:
            try:
                return int(self.publicationDate[:4])
            except ValueError:
                return None
        return None

    @computed_field
    @property
    def journal_name(self) -> str | None:
        """Container / journal name, or None when empty."""
        return self.container.name or None

    @computed_field
    @property
    def author_names(self) -> list[str]:
        """Non-empty full names of all authors."""
        return [a.fullName for a in self.authors if a.fullName]

    @computed_field
    @property
    def license(self) -> str | None:
        """First non-empty license string found across instances."""
        for inst in self.instances:
            if inst.license:
                return inst.license
        return None

    def __str__(self) -> str:
        parts = []
        if self.mainTitle:
            parts.append(self.mainTitle[:80])
        if self.publication_year:
            parts.append(f"({self.publication_year})")
        if self.doi:
            parts.append(f"DOI:{self.doi}")
        return " | ".join(parts) if parts else f"ResearchProduct(id={self.id!r})"
