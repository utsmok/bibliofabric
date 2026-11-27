# aireloom/models/scholix.py
"""Pydantic models for representing Scholix (Scholarly Link Exchange) data.

Models for the Scholexplorer API V2 and V3 response schema. V1 support was
dropped upstream ("deprecated"; v1 and v2 being phased out in favour of V3).
Reference: https://graph.openaire.eu/docs/apis/scholexplorer/api
"""

from datetime import datetime
from typing import Literal

from bibliofabric import SafeList, SafeStr
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

ScholixRelationshipNameValue = Literal[
    "IsRelatedTo",
    "References",
    "IsReferencedBy",
    "IsSupplementTo",
    "IsSupplementedBy",
    "IsSourceOf",
    "IsDerivedFrom",
    "IsVersionOf",
    "HasVersion",
    "IsPartOf",
    "IsPreviousVersionOf",
    "IsNewVersionOf",
    "IsIdenticalTo",
    "IsContinuedBy",
    "Continues",
    "IsCompiledBy",
    "Compiles",
    "IsDescribedBy",
    "Describes",
    "HasAmongTopNSimilarDocuments",
    "IsAmongTopNSimilarDocuments",
    "Reviews",
    "IsReviewedBy",
    "Cites",
    "IsCitedBy",
    "IsOriginalFormOf",
    "IsVariantFormOf",
    "IsPublishedIn",
]
"""Known relationship type names in the Scholix schema."""


class ScholixIdentifier(BaseModel):
    """A persistent identifier: ``{"ID", "IDScheme", "IDURL"}``."""

    id_val: SafeStr = Field(
        alias="ID",
        default="",
        validation_alias=AliasChoices("ID", "id", "value"),
    )
    id_scheme: SafeStr = Field(
        alias="IDScheme",
        default="",
        validation_alias=AliasChoices("IDScheme", "idScheme", "scheme", "type"),
    )
    id_url: str | None = Field(
        alias="IDURL",
        default=None,
        validation_alias=AliasChoices("IDURL", "idUrl", "url"),
    )

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class ScholixCreator(BaseModel):
    """A creator (author, contributor) of a Scholix entity."""

    name: SafeStr = Field(alias="Name", default="")
    identifier: SafeList[ScholixIdentifier] = Field(
        alias="Identifier", default_factory=list
    )

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class ScholixPublisher(BaseModel):
    """A publisher of a Scholix entity or entry from ``/v2/LinkPublisher``."""

    name: SafeStr = Field(alias="Name", default="")
    identifier: SafeList[ScholixIdentifier] = Field(
        alias="Identifier", default_factory=list
    )
    total_relationships: int | None = Field(alias="totalRelationships", default=None)

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class ScholixEntity(BaseModel):
    """A scholarly entity (source or target) in a Scholix relationship."""

    identifier: SafeList[ScholixIdentifier] = Field(
        alias="Identifier", default_factory=list
    )
    type: str | None = Field(alias="Type", default=None)
    sub_type: str | None = Field(
        alias="SubType",
        default=None,
        validation_alias=AliasChoices("subType", "SubType"),
    )
    title: SafeStr = Field(alias="Title", default="")
    creator: SafeList[ScholixCreator] = Field(alias="Creator", default_factory=list)
    publication_date: str | None = Field(alias="PublicationDate", default=None)
    publisher: SafeList[ScholixPublisher] = Field(
        alias="Publisher", default_factory=list
    )

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class ScholixRelationshipType(BaseModel):
    """The type of relationship between two Scholix entities."""

    name: ScholixRelationshipNameValue | str = Field(alias="Name", default="")
    sub_type: str | None = Field(
        alias="SubType",
        default=None,
        validation_alias=AliasChoices("subType", "SubType"),
    )
    sub_type_schema: str | None = Field(
        alias="SubTypeSchema",
        default=None,
        validation_alias=AliasChoices("subTypeSchema", "SubTypeSchema"),
    )

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class ScholixLinkProvider(BaseModel):
    """A Scholix link provider or entry from ``/v2/LinkProvider``."""

    name: SafeStr = Field(alias="Name", default="")
    identifier: SafeList[ScholixIdentifier] = Field(
        alias="Identifier", default_factory=list
    )
    total_relationships: int | None = Field(alias="totalRelationships", default=None)

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class ScholixRelationship(BaseModel):
    """A single Scholix relationship link between two scholarly entities."""

    link_provider: SafeList[ScholixLinkProvider] = Field(
        alias="LinkProvider", default_factory=list
    )
    relationship_type: ScholixRelationshipType | None = Field(
        alias="RelationshipType", default=None
    )
    source: ScholixEntity | None = Field(alias="Source", default=None)
    target: ScholixEntity | None = Field(alias="Target", default=None)
    link_publication_date: datetime | None = Field(
        alias="LinkPublicationDate",
        default=None,
        description="Date the link was published.",
    )
    license_url: str | None = Field(alias="LicenseURL", default=None)
    harvest_date: str | None = Field(alias="HarvestDate", default=None)

    model_config = ConfigDict(populate_by_name=True, extra="allow")
