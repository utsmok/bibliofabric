"""Pydantic models for Europe PMC search results and their nested structures."""

from typing import Any

from bibliofabric import SafeStr
from pydantic import BaseModel, ConfigDict, Field


class AuthorId(BaseModel):
    """One author identifier, for example ``{"type": "ORCID", "value": "..."}``."""

    model_config = ConfigDict(extra="allow")

    type: str | None = None
    value: str | None = None


class AuthorAffiliation(BaseModel):
    """One affiliation of an author."""

    model_config = ConfigDict(extra="allow")

    affiliation: str | None = None


class AuthorAffiliationDetailsList(BaseModel):
    """The affiliation list of one author (``authorAffiliationDetailsList``)."""

    model_config = ConfigDict(extra="allow")

    author_affiliation: list[AuthorAffiliation] | None = Field(
        None, alias="authorAffiliation"
    )


class Author(BaseModel):
    """One author of a Europe PMC article."""

    model_config = ConfigDict(extra="allow")

    full_name: str | None = Field(None, alias="fullName")
    last_name: str | None = Field(None, alias="lastName")
    first_name: str | None = Field(None, alias="firstName")
    initials: str | None = None
    collective_name: str | None = Field(None, alias="collectiveName")
    author_id: AuthorId | None = Field(None, alias="authorId")
    author_affiliation_details_list: AuthorAffiliationDetailsList | None = Field(
        None, alias="authorAffiliationDetailsList"
    )


class AuthorList(BaseModel):
    """The author list of a Europe PMC article (``authorList``)."""

    model_config = ConfigDict(extra="allow")

    author: list[Author] | None = None


class FullTextIdList(BaseModel):
    """The full text identifiers of an article (``fullTextIdList``)."""

    model_config = ConfigDict(extra="allow")

    full_text_id: list[str] | None = Field(None, alias="fullTextId")


class Journal(BaseModel):
    """A journal in which an article appeared."""

    model_config = ConfigDict(extra="allow")

    medline_abbreviation: str | None = Field(None, alias="medlineAbbreviation")
    title: str | None = None
    essn: str | None = None
    issn: str | None = None
    nlmid: str | None = None
    isoabbreviation: str | None = Field(None, alias="isoabbreviation")


class JournalInfo(BaseModel):
    """The journal context of an article (``journalInfo``)."""

    model_config = ConfigDict(extra="allow")

    issue: str | None = None
    volume: str | None = None
    journal_issue_id: int | None = Field(None, alias="journalIssueId")
    date_of_publication: str | None = Field(None, alias="dateOfPublication")
    month_of_publication: int | None = Field(None, alias="monthOfPublication")
    year_of_publication: int | None = Field(None, alias="yearOfPublication")
    journal: Journal | None = None
    print_publication_date: str | None = Field(None, alias="printPublicationDate")
    first_publication_date: str | None = Field(None, alias="firstPublicationDate")


class FullTextUrl(BaseModel):
    """One link to a full text representation of an article."""

    model_config = ConfigDict(extra="allow")

    availability: str | None = None
    availability_code: str | None = Field(None, alias="availabilityCode")
    document_style: str | None = Field(None, alias="documentStyle")
    site: str | None = None
    url: str | None = None


class FullTextUrlList(BaseModel):
    """The full text URL list of an article (``fullTextUrlList``)."""

    model_config = ConfigDict(extra="allow")

    full_text_url: list[FullTextUrl] | None = Field(None, alias="fullTextUrl")


class MeshQualifier(BaseModel):
    """One MeSH qualifier (subheading) of a MeSH heading."""

    model_config = ConfigDict(extra="allow")

    abbreviation: str | None = None
    qualifier_name: str | None = Field(None, alias="qualifierName")
    major_topic_yn: bool | None = Field(None, alias="majorTopic_YN")


class MeshQualifierList(BaseModel):
    """The qualifier wrapper of one MeSH heading (``meshQualifierList``)."""

    model_config = ConfigDict(extra="allow")

    mesh_qualifier: list[MeshQualifier] | None = Field(None, alias="meshQualifier")


class MeshHeading(BaseModel):
    """One MeSH heading of an article."""

    model_config = ConfigDict(extra="allow")

    major_topic_yn: bool | None = Field(None, alias="majorTopic_YN")
    mesh_qualifier_list: MeshQualifierList | None = Field(
        None, alias="meshQualifierList"
    )
    descriptor_name: str | None = Field(None, alias="descriptorName")


class MeshHeadingList(BaseModel):
    """The MeSH heading list of an article (``meshHeadingList``)."""

    model_config = ConfigDict(extra="allow")

    mesh_heading: list[MeshHeading] | None = Field(None, alias="meshHeading")


class Chemical(BaseModel):
    """One chemical mentioned by an article."""

    model_config = ConfigDict(extra="allow")

    name: str | None = None
    registry_number: str | None = Field(None, alias="registryNumber")


class ChemicalList(BaseModel):
    """The chemical list of an article (``chemicalList``)."""

    model_config = ConfigDict(extra="allow")

    chemical: list[Chemical] | None = None


class ArticleGrant(BaseModel):
    """One grant that funded an article."""

    model_config = ConfigDict(extra="allow")

    agency: str | None = None
    acronym: str | None = None
    grant_id: str | None = Field(None, alias="grantId")
    order_in: int | None = Field(None, alias="orderIn")


class GrantsList(BaseModel):
    """The grant list of an article (``grantsList``)."""

    model_config = ConfigDict(extra="allow")

    grant: list[ArticleGrant] | None = None


class CommentCorrection(BaseModel):
    """One comment or correction linked to an article."""

    model_config = ConfigDict(extra="allow")

    id: str | None = None
    source: str | None = None
    pmid: str | None = None
    pmcid: str | None = None
    notes: str | None = None
    type: str | None = None


class CommentCorrectionList(BaseModel):
    """The comment and correction list of an article (``commentCorrectionList``)."""

    model_config = ConfigDict(extra="allow")

    comment_correction: list[CommentCorrection] | None = Field(
        None, alias="commentCorrection"
    )


class DataLinksTag(BaseModel):
    """One data links tag of an article."""

    model_config = ConfigDict(extra="allow")


class DataLinksTagsList(BaseModel):
    """The data links tag wrapper of a core record (``dataLinksTagsList``)."""

    model_config = ConfigDict(extra="allow")

    data_links_tag: list[str] | None = Field(None, alias="dataLinkstag")


class Subset(BaseModel):
    """One journal subset of an article (for example Index Medicus)."""

    model_config = ConfigDict(extra="allow")

    code: str | None = None
    name: str | None = None


class SubsetList(BaseModel):
    """The subset wrapper of a core record (``subsetList``)."""

    model_config = ConfigDict(extra="allow")

    subset: list[Subset] | None = None


class KeywordList(BaseModel):
    """The keyword list of an article (``keywordList``).

    Europe PMC serves each keyword as a plain string.
    """

    model_config = ConfigDict(extra="allow")

    keyword: list[SafeStr] | None = None


class SearchResult(BaseModel):
    """One Europe PMC search result record.

    A ``resultType=lite`` record carries the scalar fields; ``resultType=core``
    fills in the nested structures. Unknown fields are kept (``extra="allow"``).
    """

    model_config = ConfigDict(extra="allow")

    id: str | None = None
    source: str | None = None
    pmid: str | None = None
    pmcid: str | None = None
    full_text_id_list: FullTextIdList | None = Field(None, alias="fullTextIdList")
    doi: str | None = None
    title: str | None = None
    author_string: str | None = Field(None, alias="authorString")
    journal_title: str | None = Field(None, alias="journalTitle")
    journal_volume: str | None = Field(None, alias="journalVolume")
    journal_issue: str | None = Field(None, alias="journalIssue")
    journal_issn: str | None = Field(None, alias="journalIssn")
    book_or_report_details: dict[str, Any] | None = Field(
        None, alias="bookOrReportDetails"
    )
    page_info: str | None = Field(None, alias="pageInfo")
    abstract_text: str | None = Field(None, alias="abstractText")
    author_list: AuthorList | None = Field(None, alias="authorList")
    affiliation: str | None = None
    publication_status: str | None = Field(None, alias="publicationStatus")
    pub_year: str | None = Field(None, alias="pubYear")
    pub_model: str | None = Field(None, alias="pubModel")
    language: str | None = None
    pub_type_list: list[str] | dict[str, list[str]] | None = Field(
        None, alias="pubTypeList"
    )
    in_epmc: SafeStr | None = Field(None, alias="inEPMC")
    in_pmc: SafeStr | None = Field(None, alias="inPMC")
    is_open_access: SafeStr | None = Field(None, alias="isOpenAccess")
    has_pdf: SafeStr | None = Field(None, alias="hasPDF")
    has_suppl: SafeStr | None = Field(None, alias="hasSuppl")
    has_data: SafeStr | None = Field(None, alias="hasData")
    has_references: SafeStr | None = Field(None, alias="hasReferences")
    has_book: SafeStr | None = Field(None, alias="hasBook")
    has_text_mined_terms: SafeStr | None = Field(None, alias="hasTextMinedTerms")
    has_db_cross_references: SafeStr | None = Field(None, alias="hasDbCrossReferences")
    has_evaluations: SafeStr | None = Field(None, alias="hasEvaluations")
    has_labs_links: SafeStr | None = Field(None, alias="hasLabsLinks")
    has_tm_accession_numbers: SafeStr | None = Field(
        None, alias="hasTMAccessionNumbers"
    )
    cited_by_count: int | None = Field(None, alias="citedByCount")
    first_publication_date: str | None = Field(None, alias="firstPublicationDate")
    first_index_date: str | None = Field(None, alias="firstIndexDate")
    date_of_creation: str | None = Field(None, alias="dateOfCreation")
    date_of_revision: str | None = Field(None, alias="dateOfRevision")
    date_of_completion: str | None = Field(None, alias="dateOfCompletion")
    full_text_received_date: str | None = Field(None, alias="fullTextReceivedDate")
    journal_info: JournalInfo | None = Field(None, alias="journalInfo")
    mesh_heading_list: MeshHeadingList | None = Field(None, alias="meshHeadingList")
    chemical_list: ChemicalList | None = Field(None, alias="chemicalList")
    keyword_list: KeywordList | None = Field(None, alias="keywordList")
    grants_list: GrantsList | None = Field(None, alias="grantsList")
    comment_correction_list: CommentCorrectionList | None = Field(
        None, alias="commentCorrectionList"
    )
    full_text_url_list: FullTextUrlList | None = Field(None, alias="fullTextUrlList")
    data_links_tags_list: DataLinksTagsList | None = Field(
        None, alias="dataLinksTagsList"
    )
    subset_list: SubsetList | None = Field(None, alias="subsetList")
    manuscript_id: str | None = Field(None, alias="manuscriptId")
    author_id_list: AuthorList | None = Field(None, alias="authorIdList")
    epmc_auth_man: bool | None = Field(None, alias="epmcAuthMan")
    auth_man: bool | None = Field(None, alias="authMan")
    nih_auth_man: bool | None = Field(None, alias="nihAuthMan")
    license: str | None = None
    HitCount: int | None = None


class SearchRequest(BaseModel):
    """The request echo that every Europe PMC search response carries."""

    model_config = ConfigDict(extra="allow")

    query_string: str | None = Field(None, alias="queryString")
    result_type: str | None = Field(None, alias="resultType")
    cursor_mark: str | None = Field(None, alias="cursorMark")
    page_size: int | None = Field(None, alias="pageSize")
    sort: str | None = None
    synonym: bool | None = None


class SearchResultList(BaseModel):
    """The result list of a search response (``resultList``)."""

    model_config = ConfigDict(extra="allow")

    result: list[SearchResult] | None = None


class SearchResponse(BaseModel):
    """The raw envelope of a ``/search`` response.

    ``ResourceClient.search()`` returns :class:`Page` objects built from this
    envelope; the model is exported for callers who want the whole envelope.
    """

    model_config = ConfigDict(extra="allow")

    version: str | None = None
    hit_count: int | None = Field(None, alias="hitCount")
    request: SearchRequest | None = None
    result_list: SearchResultList | None = Field(None, alias="resultList")
    next_cursor_mark: str | None = Field(None, alias="nextCursorMark")
    page_next_cursor_mark: str | None = Field(None, alias="pageNextCursorMark")


__all__ = [
    "Author",
    "DataLinksTag",
    "DataLinksTagsList",
    "Subset",
    "SubsetList",
    "AuthorAffiliation",
    "AuthorAffiliationDetailsList",
    "AuthorId",
    "AuthorList",
    "Chemical",
    "ChemicalList",
    "CommentCorrection",
    "CommentCorrectionList",
    "ArticleGrant",
    "GrantsList",
    "FullTextIdList",
    "FullTextUrl",
    "FullTextUrlList",
    "Journal",
    "JournalInfo",
    "KeywordList",
    "MeshHeading",
    "MeshHeadingList",
    "MeshQualifierList",
    "MeshQualifier",
    "SearchRequest",
    "SearchResponse",
    "SearchResult",
    "SearchResultList",
]
