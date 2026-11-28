"""Models for the Special:EntityData routes and the Action utility modules."""

from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from .entity import Entity


class _MiscModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class EntityDataDocument(_MiscModel):
    """A non-JSON Special:EntityData document (an RDF serialization).

    The RDF formats (`jsonld`, `rdf`, `nt`, `ttl`, `n3`) pass through as
    text; `format` is the requested suffix and `content_type` is the
    `Content-Type` the service answered with.
    """

    id: str
    format: str
    content_type: str
    text: str


class EntityDataResult(_MiscModel):
    """The typed result of an EntityData read.

    `entity` is set for `format="json"`; `document` is set for the RDF
    formats. Exactly one of the two carries the payload.
    """

    id: str
    format: str
    content_type: str
    entity: Entity | None = None
    document: EntityDataDocument | None = None


class ParsedValue(_MiscModel):
    """One parsed value of `wbparsevalue`."""

    raw: str
    value: Any
    type: str


class PropertySuggestion(_MiscModel):
    """One suggestion of `wbsgetsuggestions`."""

    id: str
    url: str | None = None
    rating: str | None = None
    label: str | None = None
    description: str | None = None


class Constraint(_MiscModel):
    """The constraint definition a check result reports against."""

    id: str
    type: str
    typeLabel: str | None = None
    link: str | None = None
    discussLink: str | None = None


class ConstraintCheckResult(_MiscModel):
    """One constraint check result of one claim."""

    status: str
    property: str
    constraint: Constraint
    message_html: str | None = Field(
        default=None, validation_alias=AliasChoices("message_html", "message-html")
    )
    claim: str | None = None


class CheckedMainsnak(_MiscModel):
    """The mainsnak wrapper of a checked claim."""

    hash: str | None = None
    results: list[ConstraintCheckResult] = []


class CheckedClaim(_MiscModel):
    """The constraint checks of one claim."""

    id: str
    mainsnak: CheckedMainsnak


ConstraintChecksByProperty = dict[str, list[CheckedClaim]]
"""Constraint checks of one entity's claims keyed by property id."""


__all__ = [
    "CheckedClaim",
    "CheckedMainsnak",
    "Constraint",
    "ConstraintCheckResult",
    "ConstraintChecksByProperty",
    "EntityDataDocument",
    "EntityDataResult",
    "ParsedValue",
    "PropertySuggestion",
]
