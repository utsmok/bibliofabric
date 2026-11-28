"""Pydantic models for Wikidata read payloads."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class _WikidataModel(BaseModel):
    """Base for all Wikidata models; unknown fields are kept, not dropped."""

    model_config = ConfigDict(extra="allow")


class Term(_WikidataModel):
    """One language-qualified label, description, or alias."""

    language: str
    value: str


class MonolingualText(_WikidataModel):
    """The ``monolingualtext`` data value of a snak."""

    language: str
    text: str


TermMap = dict[str, Term]
"""Labels or descriptions keyed by language code."""

AliasMap = dict[str, list[Term]]
"""Aliases keyed by language code."""


class DataValue(_WikidataModel):
    """The ``datavalue`` member of a snak.

    ``value`` carries one of the Wikidata value shapes (a string, an entity
    id object, a time object, a quantity object, a globe-coordinate object,
    or a monolingual-text object) depending on ``type``. The client keeps it
    untyped so no payload shape is lost; ``parse_value`` and ``parse_time``
    offer the common shapes as helpers.
    """

    value: Any
    type: str


class Snak(_WikidataModel):
    """One claim, qualifier, or reference snak."""

    snaktype: str
    property: str
    hash: str | None = None
    datavalue: DataValue | None = None
    datatype: str | None = None


class Reference(_WikidataModel):
    """The reference block of a claim."""

    hash: str
    snaks: dict[str, list[Snak]]
    snaks_order: list[str] | None = None


class Claim(_WikidataModel):
    """One statement of a Wikidata entity as returned by the Action API."""

    mainsnak: Snak
    type: str = "statement"
    rank: str
    id: str | None = None
    qualifiers: dict[str, list[Snak]] = {}
    qualifiers_order: list[str] | None = None
    references: list[Reference] = []


class Sitelink(_WikidataModel):
    """One site link of an item."""

    site: str
    title: str
    badges: list[str] = []
    url: str | None = None


SitelinkMap = dict[str, Sitelink]
"""Site links keyed by site id (``enwiki``, ``dewiki``)."""


class Entity(_WikidataModel):
    """One entity as returned by ``wbgetentities``.

    Items carry ``labels``, ``descriptions``, ``aliases``, ``claims``, and
    ``sitelinks``. Properties carry ``datatype`` and the term fields. Lexemes
    and forms carry their own shapes, which ``extra="allow"`` keeps.
    """

    type: str
    id: str
    pageid: int | None = None
    ns: int | None = None
    title: str | None = None
    lastrevid: int | None = None
    modified: str | None = None
    datatype: str | None = None
    labels: TermMap = {}
    descriptions: TermMap = {}
    aliases: AliasMap = {}
    claims: dict[str, list[Claim]] = {}
    sitelinks: SitelinkMap = {}

    def label(self, language: str = "en") -> str | None:
        """Return the label in ``language``, or ``None`` when there is none."""
        term = self.labels.get(language)
        return term.value if term is not None else None

    def description(self, language: str = "en") -> str | None:
        """Return the description in ``language``, or ``None``."""
        term = self.descriptions.get(language)
        return term.value if term is not None else None


ClaimsByProperty = dict[str, list[Claim]]
"""Claims of an entity keyed by property id, as ``wbgetclaims`` returns them."""


__all__ = [
    "AliasMap",
    "Claim",
    "ClaimsByProperty",
    "DataValue",
    "Entity",
    "MonolingualText",
    "Reference",
    "Sitelink",
    "SitelinkMap",
    "Snak",
    "Term",
    "TermMap",
]
