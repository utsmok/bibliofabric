# https://graph.openaire.eu/docs/apis/scholexplorer/v3/response_schema

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

ScholixEntityTypeName = Literal["publication", "dataset", "software", "other"]
ScholixRelationshipNameValue = Literal[
    "IsSupplementTo",
    "IsSupplementedBy",
    "References",
    "IsReferencedBy",
    "IsRelatedTo",
]


class ScholixIdentifier(BaseModel):
    id_val: str = Field(alias="ID")
    id_scheme: str = Field(alias="IDScheme")
    id_url: HttpUrl | None = Field(alias="IDURL", default=None)

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class ScholixCreator(BaseModel):
    name: str | None = Field(alias="Name", default=None)
    identifier: list[ScholixIdentifier] | None = Field(alias="Identifier", default=None)

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class ScholixPublisher(BaseModel):
    name: str = Field(alias="Name")
    identifier: list[ScholixIdentifier] | None = Field(alias="Identifier", default=None)

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class ScholixEntity(BaseModel):
    identifier: list[ScholixIdentifier] = Field(alias="Identifier")
    type: ScholixEntityTypeName = Field(alias="Type")
    sub_type: str | None = Field(alias="SubType", default=None)
    title: str | None = Field(alias="Title", default=None)
    creator: list[ScholixCreator] | None = Field(alias="Creator", default=None)
    publication_date: str | None = Field(alias="PublicationDate", default=None)
    publisher: list[ScholixPublisher] | None = Field(alias="Publisher", default=None)

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class ScholixRelationshipType(BaseModel):
    name: ScholixRelationshipNameValue = Field(alias="Name")
    sub_type: str | None = Field(alias="SubType", default=None)
    sub_type_schema: HttpUrl | None = Field(alias="SubTypeSchema", default=None)

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class ScholixLinkProvider(BaseModel):
    name: str = Field(alias="Name")
    identifier: list[ScholixIdentifier] | None = Field(alias="Identifier", default=None)

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class ScholixRelationship(BaseModel):
    link_provider: list[ScholixLinkProvider] | None = Field(
        alias="LinkProvider", default=None
    )
    relationship_type: ScholixRelationshipType = Field(alias="RelationshipType")
    source: ScholixEntity = Field(alias="Source")
    target: ScholixEntity = Field(alias="Target")
    link_publication_date: datetime | None = Field(
        alias="LinkPublicationDate",
        default=None,
        description="Date the link was published.",
    )
    license_url: HttpUrl | None = Field(alias="LicenseURL", default=None)
    harvest_date: str | None = Field(alias="HarvestDate", default=None)

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class ScholixResponse(BaseModel):
    """Response structure for the Scholexplorer Links endpoint."""

    current_page: int = Field(
        alias="currentPage", description="The current page number (0-indexed)."
    )
    total_links: int = Field(
        alias="totalLinks", description="Total number of links matching the query."
    )
    total_pages: int = Field(
        alias="totalPages", description="Total number of pages available."
    )
    result: list[ScholixRelationship] = Field(
        alias="result", description="List of Scholix relationship links."
    )

    model_config = ConfigDict(populate_by_name=True, extra="allow")
