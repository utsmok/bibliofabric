"""Pydantic models for the JSON-LD record nodes of the ISSN Portal.

Every model allows extra keys, so fields the Portal adds later stay
reachable on the instance. The raw node a model was parsed from is kept on
the ``raw`` attribute (excluded from dumps).
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

#: A JSON-LD key whose name contains characters that are no Python
#: identifiers travels under a snake_case field with a matching alias.
_CONFIG = ConfigDict(extra="allow", populate_by_name=True)


class LangString(BaseModel):
    """A language-tagged string (JSON-LD ``{"@value": ..., "@language": ...}``)."""

    value: str = Field(alias="@value")
    language: str | None = Field(default=None, alias="@language")

    model_config = _CONFIG


class TitleValue(BaseModel):
    """One title object of the ``title`` array (a ``bf:Title`` node)."""

    main_title: LangString | None = Field(default=None, alias="mainTitle")
    type: str | list[str] | None = None

    model_config = _CONFIG


class IdentifiedBy(BaseModel):
    """One identifier node.

    Full records cluster their nodes under ``#ISSN``, ``#ISSN-L`` and
    ``#KeyTitle`` keys; a cancelled record answers one flat node with
    ``cancelledInFavorOf`` and a cancelled status instead.
    """

    id: str | None = None
    status: str | None = None
    type: str | list[str] | None = None
    value: str | None = None
    has_cancelled_issn: list[str] = Field(
        default_factory=list, alias="hasCancelledISSN"
    )
    cancelled_in_favor_of: list[str] = Field(
        default_factory=list, alias="cancelledInFavorOf"
    )
    main_title: LangString | None = Field(default=None, alias="mainTitle")

    model_config = _CONFIG


class IsPartOf(BaseModel):
    """One cluster membership of the ``isPartOf`` array (an ISSN-L or ISSN-H link)."""

    id: str | None = None
    identified_by: IdentifiedBy | dict[str, IdentifiedBy] | None = Field(
        default=None, alias="identifiedBy"
    )

    model_config = _CONFIG


class GenerationActivity(BaseModel):
    """The ``generatedBy`` activity of a record (provenance)."""

    id: str | None = None
    created: str | None = None
    generated: list[str] = Field(default_factory=list)
    type: str | list[str] | None = None
    was_associated_with: str | None = Field(default=None, alias="wasAssociatedWith")

    model_config = _CONFIG


class RecordAttribution(BaseModel):
    """The ISSN centre a record is attributed to."""

    id: str | None = None
    type: str | list[str] | None = None

    model_config = _CONFIG


class RecordProvenance(BaseModel):
    """The ``mainEntityOf`` node: record status, modification date, provenance."""

    id: str | None = None
    modified: str | None = None
    status: str | None = None
    type: str | list[str] | None = None
    was_attributed_to: RecordAttribution | None = Field(
        default=None, alias="wasAttributedTo"
    )
    generated_by: GenerationActivity | None = Field(default=None, alias="generatedBy")

    model_config = _CONFIG


class SeriatimRecord(BaseModel):
    """One ISSN record node of ``/resource/ISSN/{issn}`` (JSON-LD).

    Full records carry titles, identifier nodes, cluster membership,
    provenance, and cancelled or incorrect ISSNs. Cancelled records answer a
    much smaller node with only ``@context``, ``id``, ``identifiedBy`` and
    ``mainEntityOf``; all optional fields cover both shapes, and unknown
    keys stay reachable as model extras. ``raw`` holds the untouched node.
    """

    raw: dict[str, Any] | None = Field(default=None, exclude=True, repr=False)
    id: str | None = None
    identifier: str | None = None
    format: str | None = None
    type: list[str] | None = None
    type_dct: str | None = Field(default=None, alias="typeDct")
    main_title: str | LangString | list[str | LangString] | None = Field(
        default=None, alias="mainTitle"
    )
    name: list[str] | None = None
    alternate_name: list[str] = Field(default_factory=list, alias="alternateName")
    title: list[str | TitleValue] = Field(default_factory=list)
    identified_by: IdentifiedBy | dict[str, IdentifiedBy] | None = Field(
        default=None, alias="identifiedBy"
    )
    is_part_of: list[IsPartOf] = Field(default_factory=list, alias="isPartOf")
    spatial: list[str] = Field(default_factory=list)
    url: list[str] = Field(default_factory=list)
    issn_bibo: str | None = Field(default=None, alias="issnBibo")
    issn_schema: str | None = Field(default=None, alias="issnSchema")
    has_cancelled_issn_l: list[str] = Field(
        default_factory=list, alias="hasCancelledISSN-L"
    )
    has_incorrect_issn: list[str] = Field(
        default_factory=list, alias="hasIncorrectISSN"
    )
    main_entity_of: RecordProvenance | None = Field(default=None, alias="mainEntityOf")

    model_config = _CONFIG

    @property
    def issn(self) -> str | None:
        """The ISSN of the record, from the ``#ISSN`` identifier node."""
        return self._node_value("#ISSN", "bf:Issn")

    @property
    def issn_l(self) -> str | None:
        """The ISSN-L the record belongs to, from the ``#ISSN-L`` node."""
        return self._node_value("#ISSN-L", "bf:IssnL")

    @property
    def key_title(self) -> str | None:
        """The key title of the record, from the ``#KeyTitle`` node."""
        return self._node_value("#KeyTitle", None)

    def _node_value(self, name: str, node_type: str | None) -> str | None:
        """Read ``name`` from the clustered shape or the flat cancelled shape."""
        if isinstance(self.identified_by, dict):
            node = self.identified_by.get(name)
            return node.value if node else None
        if self.identified_by is None:
            return None
        flat = self.identified_by
        if node_type is None and flat.value is not None:
            return None  # the flat cancelled shape carries no key title
        if flat.type == node_type:
            return flat.value
        return None


class HasPart(BaseModel):
    """One medium of an ISSN-L cluster (the ``hasPart`` array)."""

    format: str | None = None
    id: str | None = None
    identifier: str | None = None

    model_config = _CONFIG


class IssnLRecord(BaseModel):
    """One ISSN-L node of ``/resource/ISSN-L/{issn}`` (JSON-LD).

    The node lists the media (print, online) that share the ISSN-L in
    ``hasPart``. ``raw`` holds the untouched node.
    """

    raw: dict[str, Any] | None = Field(default=None, exclude=True, repr=False)
    id: str | None = None
    type: list[str] | None = None
    has_part: list[HasPart] = Field(default_factory=list, alias="hasPart")
    identified_by: IdentifiedBy | dict[str, IdentifiedBy] | None = Field(
        default=None, alias="identifiedBy"
    )

    model_config = _CONFIG

    @property
    def issn_l(self) -> str | None:
        """The ISSN-L value of the node."""
        if isinstance(self.identified_by, dict):
            node = self.identified_by.get("#ISSN-L")
            return node.value if node else None
        return self.identified_by.value if self.identified_by else None


__all__ = [
    "GenerationActivity",
    "HasPart",
    "IdentifiedBy",
    "IsPartOf",
    "IssnLRecord",
    "LangString",
    "RecordAttribution",
    "RecordProvenance",
    "TitleValue",
    "SeriatimRecord",
]
