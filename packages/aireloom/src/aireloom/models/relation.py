"""Models for Graph API relation endpoints (``/research-products/links``)."""

from bibliofabric import SafeList, SafeStr
from pydantic import BaseModel, ConfigDict, Field


class Identifier(BaseModel):
    """An identifier with id, scheme, and url."""

    id: str | None = None
    idScheme: str | None = None
    idUrl: str | None = None

    model_config = ConfigDict(extra="allow")


class EntityRef(BaseModel):
    """Named entity with identifiers (authors, collectedFrom)."""

    name: SafeStr = ""
    identifiers: SafeList[Identifier] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


class Node(BaseModel):
    """A node (source or target) in a relation link."""

    title: SafeStr = ""
    type: str | None = None
    instanceType: str | None = None
    publicationDate: str | None = None
    identifiers: SafeList[Identifier] = Field(default_factory=list)
    authors: SafeList[EntityRef] = Field(default_factory=list)
    collectedFrom: SafeList[EntityRef] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


class RelType(BaseModel):
    """Relation type information."""

    name: str | None = None
    type: str | None = None
    typeSchema: str | None = None

    model_config = ConfigDict(extra="allow")


class Relation(BaseModel):
    """A single relation link between two scholarly entities."""

    source: Node | None = None
    target: Node | None = None
    relType: RelType | None = None
    provenance: SafeList[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


class RelationInfo(BaseModel):
    """One entry of ``/research-products/links/relations-info``."""

    relation: SafeStr = ""
    inverse: SafeStr = ""
    description: SafeStr = ""
    descriptionInverse: SafeStr = ""

    model_config = ConfigDict(extra="allow")
