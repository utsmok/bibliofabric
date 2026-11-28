"""Models for the ORCID search routes."""

from bibliofabric import SafeList, SafeStr
from pydantic import BaseModel, ConfigDict, Field

from .common import OrcidId


class ExpandedResult(BaseModel):
    """One result of ``/expanded-search``.

    ``given_names`` and ``family_names`` are plural here, unlike the person
    section. ``other_name``, ``email``, and ``institution_name`` are lists of
    plain strings.
    """

    orcid_id: SafeStr | None = Field(default=None, alias="orcid-id")
    given_names: SafeStr | None = Field(default=None, alias="given-names")
    family_names: SafeStr | None = Field(default=None, alias="family-names")
    credit_name: SafeStr | None = Field(default=None, alias="credit-name")
    other_name: SafeList[str] = Field(default_factory=list, alias="other-name")
    email: SafeList[str] = Field(default_factory=list)
    institution_name: SafeList[str] = Field(
        default_factory=list, alias="institution-name"
    )

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class SolrResult(BaseModel):
    """One result of the Solr-compatible ``/search`` route."""

    orcid_identifier: OrcidId | None = Field(default=None, alias="orcid-identifier")

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class ExpandedSearchEnvelope(BaseModel):
    """The raw ``/expanded-search`` envelope, when read directly."""

    expanded_result: SafeList[ExpandedResult] = Field(
        default_factory=list, alias="expanded-result"
    )
    num_found: int | None = Field(default=None, alias="num-found")

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class SolrSearchEnvelope(BaseModel):
    """The raw ``/search`` envelope, when read directly."""

    result: SafeList[SolrResult] = Field(default_factory=list)
    num_found: int | None = Field(default=None, alias="num-found")

    model_config = ConfigDict(extra="allow", populate_by_name=True)


__all__ = [
    "ExpandedResult",
    "ExpandedSearchEnvelope",
    "SolrResult",
    "SolrSearchEnvelope",
]
