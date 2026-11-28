"""Pydantic models for the Europe PMC profile and fields endpoints."""

from pydantic import BaseModel, ConfigDict, Field


class ProfileSourceCount(BaseModel):
    """One per-source article count of a profile (``profileList.source``)."""

    model_config = ConfigDict(extra="allow")

    name: str | None = None
    count: int | None = None


class ProfileList(BaseModel):
    """The count lists of a profile answer (``profileList``)."""

    model_config = ConfigDict(extra="allow")

    source: list[ProfileSourceCount] | None = None
    pub_type: list[ProfileSourceCount] | None = Field(None, alias="pubType")
    subset: list[ProfileSourceCount] | None = None


class ProfileRequest(BaseModel):
    """The request echo of a profile answer."""

    model_config = ConfigDict(extra="allow")

    query_string: str | None = Field(None, alias="queryString")
    profile_type: str | None = Field(None, alias="profileType")
    synonym: bool | None = None


class ProfileResponse(BaseModel):
    """The answer of the ``/profile`` endpoint for one author or grant query."""

    model_config = ConfigDict(extra="allow")

    version: str | None = None
    request: ProfileRequest | None = None
    profile_list: ProfileList | None = Field(None, alias="profileList")


class SearchTerm(BaseModel):
    """One searchable index term of the ``/fields`` endpoint."""

    model_config = ConfigDict(extra="allow")

    term: str | None = None


class SearchTermList(BaseModel):
    """The term list of a ``/fields`` answer (``searchTermList``)."""

    model_config = ConfigDict(extra="allow")

    search_terms: list[SearchTerm] | None = Field(None, alias="searchTerms")


class FieldsResponse(BaseModel):
    """The answer of the ``/fields`` endpoint: the searchable index terms."""

    model_config = ConfigDict(extra="allow")

    version: str | None = None
    search_term_list: SearchTermList | None = Field(None, alias="searchTermList")


__all__ = [
    "FieldsResponse",
    "ProfileList",
    "ProfileResponse",
    "ProfileSourceCount",
    "SearchTerm",
    "SearchTermList",
]
