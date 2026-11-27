# aireloom/models/person.py
"""Pydantic models for representing OpenAIRE Person entities.

Reference: https://api.openaire.eu/graph/v3/persons
"""

from bibliofabric import SafeList, SafeStr
from pydantic import BaseModel, ConfigDict, Field, computed_field

from .._helpers import extract_orcid
from .base import BaseEntity, CodeLabel, TypedPid


class PersonTopic(BaseModel):
    """A research topic/subject of a person (``schema`` is the wire key)."""

    value: str | None = None
    scheme: str | None = Field(default=None, alias="schema")
    fromYear: str | None = None
    toYear: str | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Measure(BaseModel):
    """A person indicator measure: ``{"id", "unit": [{code, label}]}``."""

    id: str | None = None
    unit: SafeList[CodeLabel] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


class Concept(BaseModel):
    """A concept entry inside a person's affiliation context category."""

    id: str | None = None
    label: SafeStr = ""

    model_config = ConfigDict(extra="allow")


class Category(BaseModel):
    """A category entry inside a person's affiliation context."""

    id: str | None = None
    label: SafeStr = ""
    concept: SafeList[Concept] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


class Context(BaseModel):
    """Affiliation context of a person."""

    id: str | None = None
    label: SafeStr = ""
    type: str | None = None
    category: SafeList[Category | str] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


class Person(BaseEntity):
    """Model representing an OpenAIRE Person entity.

    Captures names, identifiers (``pid`` items are ``{value, typeCode,
    typeLabel}``, e.g. ORCID), biography, topics, measures, context, and
    co-authors. Inherits the ``id`` field from ``BaseEntity``.

    Reference: https://graph.openaire.eu/docs/api/entities/person
    """

    originalId: SafeList[str] = Field(default_factory=list)
    pid: SafeList[TypedPid] = Field(default_factory=list)
    givenName: SafeStr = ""
    familyName: SafeStr = ""
    alternativeNames: SafeList[str] = Field(default_factory=list)
    biography: SafeStr = ""
    subject: SafeList[PersonTopic] = Field(default_factory=list)
    indicator: SafeList[Measure] = Field(default_factory=list)
    context: SafeList[Context] = Field(default_factory=list)
    consent: bool | None = None
    coAuthors: SafeList[str] = Field(default_factory=list)

    @computed_field
    @property
    def orcid(self) -> str | None:
        return extract_orcid(self.originalId, self.id, self.pid)

    @computed_field
    @property
    def full_name(self) -> str:
        parts = [n for n in (self.givenName, self.familyName) if n]
        return " ".join(parts)

    def __str__(self) -> str:
        name = self.full_name
        if name and self.orcid:
            return f"{name} (ORCID:{self.orcid})"
        if name:
            return name
        return f"Person(id={self.id!r})"
