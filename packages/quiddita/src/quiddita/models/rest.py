"""Models for the Wikibase REST API (``/w/rest.php/wikibase/v1``).

Verified against the live API on 2026-11-27. Note that REST entity payloads
differ from the Action API: labels and descriptions are language-to-string
maps, aliases are language-to-list-of-strings maps, and statement values wrap
their content in ``{"type": ..., "content": ...}`` objects.
"""

from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class _RestModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class RestTerm(_RestModel):
    """One language-qualified label or description."""

    language: str
    value: str


class RestTermResponse(_RestModel):
    """The body of ``/labels/{language_code}`` and sibling routes."""

    language: str
    value: str
    language_fallback_order: list[str] | None = None


class RestReferenceValue(_RestModel):
    """The typed value of a snak part in the REST shape.

    ``content`` is absent when ``type`` is ``somevalue`` or ``novalue``.
    """

    type: str
    content: Any = None


class RestQualifierProperty(_RestModel):
    """The property reference of a REST qualifier."""

    id: str
    data_type: str | None = None


class RestQualifier(_RestModel):
    """One qualifier or reference part in the REST shape."""

    property: RestQualifierProperty
    value: RestReferenceValue


class RestReference(_RestModel):
    """One reference block of a REST statement."""

    hash: str
    parts: list[RestQualifier]


class RestStatement(_RestModel):
    """One statement in the REST shape."""

    id: str
    rank: str
    property: RestQualifierProperty | str | None = None
    value: RestReferenceValue | None = None
    qualifiers: list[RestQualifier] = []
    references: list[RestReference] = []


StatementsByProperty = dict[str, list[RestStatement]]
"""Statements keyed by property id, as the REST statements route returns them."""


class RestSitelink(_RestModel):
    """One site link in the REST shape."""

    title: str
    badges: list[str] = []
    url: str | None = None


class RestItem(_RestModel):
    """An item in the REST shape (``/entities/items/{item_id}``)."""

    id: str
    type: str | None = None
    labels: dict[str, str] = {}
    descriptions: dict[str, str] = {}
    aliases: dict[str, list[str]] = {}
    statements: dict[str, list[RestStatement]] = {}
    sitelinks: dict[str, RestSitelink] = {}

    def label(self, language: str = "en") -> str | None:
        """Return the label in ``language``, or ``None`` when there is none."""
        return self.labels.get(language)

    def description(self, language: str = "en") -> str | None:
        """Return the description in ``language``, or ``None``."""
        return self.descriptions.get(language)


class RestProperty(_RestModel):
    """A property in the REST shape (``/entities/properties/{property_id}``)."""

    id: str
    type: str | None = None
    datatype: str | None = None
    labels: dict[str, str] = {}
    descriptions: dict[str, str] = {}
    aliases: dict[str, list[str]] = {}
    statements: dict[str, list[RestStatement]] = {}

    def label(self, language: str = "en") -> str | None:
        """Return the label in ``language``, or ``None`` when there is none."""
        return self.labels.get(language)


class RestSearchResult(_RestModel):
    """One hit of ``/search/items`` or ``/search/properties``."""

    id: str
    display_label: RestTerm = Field(
        validation_alias=AliasChoices("display_label", "display-label")
    )
    description: RestTerm | None = None
    match: dict[str, str] | None = None


class RestLexemeForm(_RestModel):
    """One form of a lexeme in the REST shape."""

    id: str
    representations: dict[str, str] = {}
    grammatical_features: list[str] = []
    statements: dict[str, list[RestStatement]] = {}


class RestLexemeSense(_RestModel):
    """One sense of a lexeme in the REST shape."""

    id: str
    glosses: dict[str, str] = {}
    statements: dict[str, list[RestStatement]] = {}


class RestLexeme(_RestModel):
    """A lexeme in the REST shape (``wikibaselexeme/v0/entities/lexemes/{id}``).

    ``lexical_category`` and ``language`` are bare item ids here, unlike the
    ``wbgetentities`` lexeme payload where they are nested objects.
    """

    id: str
    lemmas: dict[str, str] = {}
    lexical_category: str | None = None
    language: str | None = None
    statements: dict[str, list[RestStatement]] = {}
    forms: list[RestLexemeForm] = []
    senses: list[RestLexemeSense] = []


__all__ = [
    "RestItem",
    "RestLexeme",
    "RestLexemeForm",
    "RestLexemeSense",
    "RestProperty",
    "RestQualifier",
    "RestQualifierProperty",
    "RestReference",
    "RestReferenceValue",
    "RestSearchResult",
    "RestSitelink",
    "RestStatement",
    "RestTerm",
    "RestTermResponse",
    "StatementsByProperty",
]
