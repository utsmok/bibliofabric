"""Typed models for the JSON representations of content negotiation.

CSL JSON and DataCite JSON are large open schemas; the models pin the
fields that identify the record and allow every other field through
(``extra="allow"``). The schema.org JSON-LD dialect has a variable shape,
so only its identity fields are pinned too.
"""

from pydantic import BaseModel, ConfigDict, Field


class CslItem(BaseModel):
    """One CSL JSON item (``application/vnd.citationstyles.csl+json``)."""

    id: str | None = None
    type: str | None = None
    DOI: str | None = None
    URL: str | None = None
    title: str | None = None
    container_title: str | None = Field(default=None, alias="container-title")

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class DataciteRecord(BaseModel):
    """One DataCite JSON record (``application/vnd.datacite.datacite+json``)."""

    id: str | None = None
    doi: str | None = None
    url: str | None = None
    publisher: str | dict[str, str] | None = None
    publication_year: int | None = Field(default=None, alias="publicationYear")
    titles: list[dict[str, str]] | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class SchemaOrgThing(BaseModel):
    """One schema.org JSON-LD document (``application/vnd.schemaorg.ld+json``)."""

    context: str | None = Field(default=None, alias="@context")
    type: str | None = Field(default=None, alias="@type")
    id: str | None = Field(default=None, alias="@id")
    name: str | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)
