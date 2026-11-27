"""Base Pydantic models for OpenAIRE API entities.

This module defines foundational Pydantic models shared across the ``aireloom``
library, including :class:`BaseEntity`, persistent identifier shapes, funding
hierarchies, and null-tolerant type aliases.
"""

from typing import Annotated

from bibliofabric import SafeList, SafeStr
from pydantic import BaseModel, BeforeValidator, Field
from pydantic.config import ConfigDict


class BaseEntity(BaseModel):
    """A base Pydantic model for OpenAIRE entities (e.g., publication, project).

    This model provides a common foundation for all specific entity types,
    primarily by ensuring an `id` field is present, which is a common
    identifier across most OpenAIRE entities. It allows extra fields from the
    API to be captured without causing validation errors.

    Attributes:
        id: The unique identifier for the entity.
    """

    # Common identifier across most entities
    id: SafeStr = ""

    def __repr__(self) -> str:
        cls = type(self).__name__
        parts = []
        if self.id:
            parts.append(f"id={self.id!r}")
        type_val = getattr(self, "type", None)
        if isinstance(type_val, Pid):
            if type_val.value:
                parts.append(f"type={type_val.value!r}")
        elif type_val:
            parts.append(f"type={type_val!r}")
        return f"{cls}({', '.join(parts)})"

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Pid(BaseModel):
    """A scheme/value persistent identifier (``{"scheme": "doi", "value": ...}`)."""

    scheme: SafeStr = ""
    value: SafeStr = ""

    model_config = ConfigDict(extra="allow")


class TypedPid(BaseModel):
    """A typed identifier: ``{"value", "typeCode", "typeLabel"}`` (person/project pids)."""

    value: SafeStr = ""
    typeCode: SafeStr = ""
    typeLabel: SafeStr = ""

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class CodeLabel(BaseModel):
    """A code/label pair (countries, jurisdictions, EOSC types, communities)."""

    code: SafeStr = ""
    label: SafeStr = ""

    model_config = ConfigDict(extra="allow")


class Provenance(BaseModel):
    """Provenance/trust metadata attached to subjects, author pids and links."""

    provenance: SafeStr = ""
    trust: SafeStr = ""

    model_config = ConfigDict(extra="allow")


class DsRef(BaseModel):
    """A data-source reference in related-record ``collectedfrom`` entries."""

    dsId: SafeStr = ""
    dsName: SafeStr = ""

    model_config = ConfigDict(extra="allow")


class RelatedRecordHeader(BaseModel):
    """Header of a related-record link entry (RP ``links[]``, Project ``links[]``)."""

    relationType: SafeStr = ""
    relationClass: SafeStr = ""
    relatedIdentifier: SafeStr = ""
    relatedRecordType: SafeStr = ""
    relationProvenance: SafeStr = ""
    trust: SafeStr = ""

    model_config = ConfigDict(extra="allow")


class FundingJurisdiction(BaseModel):
    """Jurisdiction info within the hierarchical ``funding`` field."""

    code: SafeStr = ""
    label: SafeStr = ""

    model_config = ConfigDict(extra="allow")


SafeFundingJurisdiction = Annotated[
    FundingJurisdiction,
    BeforeValidator(lambda v: FundingJurisdiction() if v is None else v),
]


class FundingFunder(BaseModel):
    """Funder details within the hierarchical ``funding`` field."""

    id: SafeStr = ""
    shortname: SafeStr = ""
    name: SafeStr = ""
    jurisdiction: SafeFundingJurisdiction = Field(default_factory=FundingJurisdiction)
    pid: SafeList[Pid] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


SafeFundingFunder = Annotated[
    FundingFunder, BeforeValidator(lambda v: FundingFunder() if v is None else v)
]


class FundingLevel(BaseModel):
    """A single hierarchy level (level0/level1/level2) in the ``funding`` field."""

    id: SafeStr = ""
    description: SafeStr = ""
    name: SafeStr = ""

    model_config = ConfigDict(extra="allow")


SafeFundingLevel = Annotated[
    FundingLevel, BeforeValidator(lambda v: FundingLevel() if v is None else v)
]


class FundingHierarchy(BaseModel):
    """Funder -> level0 -> level1 -> level2 taxonomy tree (``funding`` field).

    Shared by Project.funding, Organization.fundings[] and related records.
    """

    funder: SafeFundingFunder = Field(default_factory=FundingFunder)
    level0: SafeFundingLevel = Field(default_factory=FundingLevel)
    level1: SafeFundingLevel = Field(default_factory=FundingLevel)
    level2: SafeFundingLevel = Field(default_factory=FundingLevel)

    model_config = ConfigDict(extra="allow")


class CfHbKeyValue(BaseModel):
    """A key/value pair used for ``collectedFrom``-style fields.

    OpenAIRE encodes these as ``{"key": "<dataSourceId>::<internalKey>",
    "value": "<dataSourceName>"}``. Shared across entities that expose a
    ``collectedFrom`` collection (organizations, data sources).
    """

    key: SafeStr = ""
    value: SafeStr = ""

    model_config = ConfigDict(extra="allow")


SafeCfHbKeyValue = Annotated[
    CfHbKeyValue, BeforeValidator(lambda v: CfHbKeyValue() if v is None else v)
]
SafePid = Annotated[Pid, BeforeValidator(lambda v: Pid() if v is None else v)]
SafeCodeLabel = Annotated[
    CodeLabel, BeforeValidator(lambda v: CodeLabel() if v is None else v)
]
SafeDsRef = Annotated[DsRef, BeforeValidator(lambda v: DsRef() if v is None else v)]
SafeRelatedRecordHeader = Annotated[
    RelatedRecordHeader,
    BeforeValidator(lambda v: RelatedRecordHeader() if v is None else v),
]
SafeFundingHierarchy = Annotated[
    FundingHierarchy, BeforeValidator(lambda v: FundingHierarchy() if v is None else v)
]
