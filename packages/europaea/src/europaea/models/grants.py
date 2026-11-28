"""Pydantic models for the Europe PMC grants (Grist) API."""

from pydantic import BaseModel, ConfigDict, Field


class GrantFunder(BaseModel):
    """The funder of a grant (``Funder``)."""

    model_config = ConfigDict(extra="allow")

    name: str | None = Field(None, alias="Name")
    pub_med_search_term: str | None = Field(None, alias="pubMedSearchTerm")


class GrantInfo(BaseModel):
    """One grant record (``Grant``) of the Grist database."""

    model_config = ConfigDict(extra="allow")

    id: str | None = Field(None, alias="Id")
    doi: str | None = Field(None, alias="Doi")
    title: str | None = Field(None, alias="Title")
    abstract_text: str | None = Field(None, alias="Abstract")
    start_date: str | None = Field(None, alias="StartDate")
    end_date: str | None = Field(None, alias="EndDate")
    funder: GrantFunder | None = Field(None, alias="Funder")
    grant_id: str | None = Field(None, alias="GrantId")
    amount: str | None = Field(None, alias="Amount")
    currency: str | None = Field(None, alias="CurrencyCode")


class GrantPerson(BaseModel):
    """One person associated with a grant (``Person``)."""

    model_config = ConfigDict(extra="allow")

    family_name: str | None = Field(None, alias="FamilyName")
    given_name: str | None = Field(None, alias="GivenName")
    initials: str | None = Field(None, alias="Initials")
    title: str | None = Field(None, alias="Title")
    orcid: str | None = Field(None, alias="ORCID")
    affiliation: str | None = Field(None, alias="Affiliation")


class GrantRecord(BaseModel):
    """One record of the Grist answer (``RecordList.Record``)."""

    model_config = ConfigDict(extra="allow")

    person: GrantPerson | None = Field(None, alias="Person")
    grant: GrantInfo | None = Field(None, alias="Grant")


class GrantsRequest(BaseModel):
    """The request echo of a Grist answer (``Request``)."""

    model_config = ConfigDict(extra="allow")

    query: str | None = Field(None, alias="Query")
    result_type: str | None = Field(None, alias="ResultType")
    page: str | None = Field(None, alias="Page")


class GrantRecordList(BaseModel):
    """The record list of a Grist answer (``RecordList``)."""

    model_config = ConfigDict(extra="allow")

    record: list[GrantRecord] | None = Field(None, alias="Record")


class GrantsResponse(BaseModel):
    """The raw envelope of a Grist ``/get`` answer."""

    model_config = ConfigDict(extra="allow")

    hit_count: str | None = Field(None, alias="HitCount")
    request: GrantsRequest | None = Field(None, alias="Request")
    record_list: GrantRecordList | None = Field(None, alias="RecordList")


__all__ = [
    "GrantFunder",
    "GrantInfo",
    "GrantPerson",
    "GrantRecord",
    "GrantRecordList",
    "GrantsRequest",
    "GrantsResponse",
]
