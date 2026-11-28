"""Pydantic models for the per-article Europe PMC routes."""

from bibliofabric import SafeStr
from pydantic import BaseModel, ConfigDict, Field


class ListRequest(BaseModel):
    """The request echo of a paged per-article route (references, citations)."""

    model_config = ConfigDict(extra="allow")

    id: str | None = None
    source: str | None = None
    off_set: int | None = Field(None, alias="offSet")
    page_size: int | None = Field(None, alias="pageSize")
    semantic_type: str | None = Field(None, alias="semanticType")


class Citation(BaseModel):
    """One reference or citation of an article.

    The ``/references`` and ``/citations`` routes return the same record
    shape; unknown fields are kept.
    """

    model_config = ConfigDict(extra="allow")

    id: str | None = None
    source: str | None = None
    pmid: str | None = None
    pmcid: str | None = None
    citation_type: str | None = Field(None, alias="citationType")
    title: str | None = None
    author_string: str | None = Field(None, alias="authorString")
    journal_abbreviation: str | None = Field(None, alias="journalAbbreviation")
    issn: str | None = None
    essn: str | None = None
    issue: str | None = None
    volume: str | None = None
    pub_year: int | None = Field(None, alias="pubYear")
    page_info: str | None = Field(None, alias="pageInfo")
    cited_by_count: int | None = Field(None, alias="citedByCount")
    cited_order: int | None = Field(None, alias="citedOrder")
    match: str | None = None
    doi: str | None = None
    abstract_text: str | None = Field(None, alias="abstractText")
    pub_year_iso: str | None = Field(None, alias="pubYearISO")


class ReferenceList(BaseModel):
    """The reference list of a ``/references`` response (``referenceList``)."""

    model_config = ConfigDict(extra="allow")

    reference: list[Citation] | None = None


class CitationList(BaseModel):
    """The citation list of a ``/citations`` response (``citationList``)."""

    model_config = ConfigDict(extra="allow")

    citation: list[Citation] | None = None


class ReferencesResponse(BaseModel):
    """The raw envelope of a ``/{source}/{id}/references`` response."""

    model_config = ConfigDict(extra="allow")

    version: str | None = None
    hit_count: int | None = Field(None, alias="hitCount")
    request: ListRequest | None = None
    reference_list: ReferenceList | None = Field(None, alias="referenceList")


class CitationsResponse(BaseModel):
    """The raw envelope of a ``/{source}/{id}/citations`` response."""

    model_config = ConfigDict(extra="allow")

    version: str | None = None
    hit_count: int | None = Field(None, alias="hitCount")
    request: ListRequest | None = None
    citation_list: CitationList | None = Field(None, alias="citationList")


class DatabaseLink(BaseModel):
    """One database cross-reference of an article."""

    model_config = ConfigDict(extra="allow")

    accession_id: str | None = Field(None, alias="accessionId")
    database: str | None = None
    db_name: str | None = Field(None, alias="dbName")


class DatabaseLinkList(BaseModel):
    """The database link list of a ``/databaseLinks`` response."""

    model_config = ConfigDict(extra="allow")

    database_link: list[DatabaseLink] | None = Field(None, alias="databaseLink")


class DatabaseLinksResponse(BaseModel):
    """The raw envelope of a ``/{source}/{id}/databaseLinks`` response."""

    model_config = ConfigDict(extra="allow")

    version: str | None = None
    hit_count: int | None = Field(None, alias="hitCount")
    request: ListRequest | None = None
    database_link_list: DatabaseLinkList | None = Field(None, alias="databaseLinkList")


class LinkIdentifier(BaseModel):
    """One identifier inside a data link (``Identifier``)."""

    model_config = ConfigDict(extra="allow")

    id: str | None = Field(None, alias="ID")
    id_scheme: str | None = Field(None, alias="IDScheme")
    id_url: str | None = Field(None, alias="IDURL")


class LinkType(BaseModel):
    """The object type of a data link end (``Type``)."""

    model_config = ConfigDict(extra="allow")

    name: str | None = Field(None, alias="Name")


class LinkSource(BaseModel):
    """The article end of a data link (``Source``)."""

    model_config = ConfigDict(extra="allow")

    identifier: LinkIdentifier | None = Field(None, alias="Identifier")
    type: LinkType | None = Field(None, alias="Type")


class LinkPublisher(BaseModel):
    """The publisher of a data link target (``Publisher``)."""

    model_config = ConfigDict(extra="allow")

    name: str | None = Field(None, alias="Name")


class LinkTarget(BaseModel):
    """The target end of a data link (``Target``)."""

    model_config = ConfigDict(extra="allow")

    identifier: LinkIdentifier | None = Field(None, alias="Identifier")
    type: LinkType | None = Field(None, alias="Type")
    title: str | None = Field(None, alias="Title")
    publisher: LinkPublisher | None = None
    image_url: str | None = Field(None, alias="ImageURL")


class LinkProvider(BaseModel):
    """The provider that reported a data link (``LinkProvider``)."""

    model_config = ConfigDict(extra="allow")

    name: str | None = Field(None, alias="Name")


class RelationshipType(BaseModel):
    """The relationship type of a data link (``RelationshipType``)."""

    model_config = ConfigDict(extra="allow")

    name: str | None = Field(None, alias="Name")


class DataLinkRecord(BaseModel):
    """One data link record (``Link``) inside a ``/datalinks`` response."""

    model_config = ConfigDict(extra="allow")

    publication_date: str | None = Field(None, alias="PublicationDate")
    relationship_type: RelationshipType | None = Field(None, alias="RelationshipType")
    obtained_by: str | None = Field(None, alias="ObtainedBy")
    source: LinkSource | None = Field(None, alias="Source")
    target: LinkTarget | None = Field(None, alias="Target")
    link_provider: LinkProvider | None = Field(None, alias="LinkProvider")


class DataLinkList(BaseModel):
    """The link list of one data link section (``Linklist``)."""

    model_config = ConfigDict(populate_by_name=True)

    link: list[DataLinkRecord] | None = Field(None, alias="Link")


class DataLinkSection(BaseModel):
    """One section of a data link category (``Section``)."""

    model_config = ConfigDict(extra="allow")

    obtained_by: str | None = Field(None, alias="ObtainedBy")
    section_link_count: int | None = Field(None, alias="SectionLinkCount")
    tags: list[str] | None = Field(None, alias="Tags")
    linklist: DataLinkList | None = Field(None, alias="Linklist")


class DataLinkCategory(BaseModel):
    """One category of data links (``Category``), for example ``Altmetric``."""

    model_config = ConfigDict(extra="allow")

    name: str | None = Field(None, alias="Name")
    category_link_count: int | None = Field(None, alias="CategoryLinkCount")
    section: list[DataLinkSection] | None = Field(None, alias="Section")


class DataLinkListEnvelope(BaseModel):
    """The data link list of a ``/datalinks`` response (``dataLinkList``)."""

    model_config = ConfigDict(extra="allow")

    category: list[DataLinkCategory] | None = Field(None, alias="Category")


class DataLinksRequest(BaseModel):
    """The request echo of a ``/datalinks`` response."""

    model_config = ConfigDict(extra="allow")

    id: str | None = None
    source: str | None = None


class DataLinksResponse(BaseModel):
    """The raw envelope of a ``/{source}/{id}/datalinks`` response."""

    model_config = ConfigDict(extra="allow")

    version: str | None = None
    hit_count: int | None = Field(None, alias="hitCount")
    request: DataLinksRequest | None = None
    data_link_list: DataLinkListEnvelope | None = Field(None, alias="dataLinkList")


class LabsLinkProvider(BaseModel):
    """One provider in the ``/labsLinks`` counts (``provider``)."""

    model_config = ConfigDict(extra="allow")

    provider_name: str | None = Field(None, alias="providerName")
    links_count: int | None = Field(None, alias="linksCount")


class LabsLinksCountList(BaseModel):
    """The provider count list of a ``/labsLinks`` response."""

    model_config = ConfigDict(extra="allow")

    provider: list[LabsLinkProvider] | None = None


class LabsLinksResponse(BaseModel):
    """The raw envelope of a ``/{source}/{id}/labsLinks`` response."""

    model_config = ConfigDict(extra="allow")

    version: str | None = None
    hit_count: int | None = Field(None, alias="hitCount")
    request: ListRequest | None = None
    links_count_list: LabsLinksCountList | None = Field(None, alias="linksCountList")


class Evaluation(BaseModel):
    """One evaluation record (community peer review) of an article."""

    model_config = ConfigDict(extra="allow")


class EvaluationList(BaseModel):
    """The evaluation list of an ``/evaluations`` response."""

    model_config = ConfigDict(extra="allow")

    evaluation: list[Evaluation] | None = None


class EvaluationsResponse(BaseModel):
    """The raw envelope of an ``/evaluations/{source}/{id}`` response."""

    model_config = ConfigDict(extra="allow")

    version: str | None = None
    evaluation_list: EvaluationList | None = Field(None, alias="evaluationList")


class XmlDocument(BaseModel):
    """A typed wrapper around one XML document answer.

    ``xml`` carries the document text (JATS article XML for ``fullTextXML``,
    book XML for ``bookXML``). The route-level extras appear when the API
    answers a small wrapper document instead of the real text (for example a
    non-open-access book id).
    """

    model_config = ConfigDict(extra="allow")

    xml: str
    is_open_access: SafeStr | None = Field(None, alias="isOpenAccess")
    message: str | None = None


__all__ = [
    "Citation",
    "CitationList",
    "CitationsResponse",
    "DataLinkCategory",
    "DataLinkList",
    "DataLinkListEnvelope",
    "DataLinkRecord",
    "DataLinkSection",
    "DataLinksRequest",
    "DataLinksResponse",
    "DatabaseLink",
    "DatabaseLinkList",
    "DatabaseLinksResponse",
    "Evaluation",
    "EvaluationList",
    "EvaluationsResponse",
    "LabsLinkProvider",
    "LabsLinksCountList",
    "LabsLinksResponse",
    "LinkIdentifier",
    "LinkProvider",
    "LinkPublisher",
    "LinkSource",
    "LinkTarget",
    "LinkType",
    "ListRequest",
    "ReferenceList",
    "ReferencesResponse",
    "RelationshipType",
    "XmlDocument",
]
