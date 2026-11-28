"""Models shared across ORCID sections."""

from bibliofabric import SafeStr
from pydantic import BaseModel, ConfigDict, Field

from .values import IntValue, TextValue


class OrcidId(BaseModel):
    """One ORCID identifier triple (``uri``, ``path``, ``host``)."""

    uri: SafeStr | None = None
    path: SafeStr | None = None
    host: SafeStr | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Source(BaseModel):
    """Who asserted a claim: a researcher, a client, or both.

    ``source_orcid`` names the researcher account, ``source_client_id`` the
    API client, and ``assertion_origin_*`` the original claimant when the
    assertion was imported.
    """

    source_orcid: OrcidId | None = Field(default=None, alias="source-orcid")
    source_client_id: OrcidId | None = Field(default=None, alias="source-client-id")
    source_name: TextValue | None = Field(default=None, alias="source-name")
    assertion_origin_orcid: OrcidId | None = Field(
        default=None, alias="assertion-origin-orcid"
    )
    assertion_origin_client_id: OrcidId | None = Field(
        default=None, alias="assertion-origin-client-id"
    )
    assertion_origin_name: TextValue | None = Field(
        default=None, alias="assertion-origin-name"
    )

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class FuzzyDate(BaseModel):
    """A date that may carry only some of year, month, and day.

    Each part is a ``{"value": "2020"}`` wrapper, because ORCID keeps the
    calendar parts as text.
    """

    year: TextValue | None = None
    month: TextValue | None = None
    day: TextValue | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    def iso(self) -> str:
        """Return the date as ``YYYY``, ``YYYY-MM``, or ``YYYY-MM-DD``."""
        parts = [
            part.text if part is not None and part.text else ""
            for part in (self.year, self.month, self.day)
        ]
        return "-".join(part for part in parts if part)


class ExternalId(BaseModel):
    """One external identifier attached to an ORCID element.

    ``type`` is for example ``doi``, ``issn``, ``pmid``, or ``grant_number``.
    ``normalized`` is the identifier in ORCID's canonical spelling.
    """

    type: SafeStr | None = Field(default=None, alias="external-id-type")
    value: SafeStr | None = Field(default=None, alias="external-id-value")
    normalized: TextValue | None = Field(default=None, alias="external-id-normalized")
    normalized_error: str | None = Field(
        default=None, alias="external-id-normalized-error"
    )
    url: TextValue | None = Field(default=None, alias="external-id-url")
    relationship: SafeStr | None = Field(default=None, alias="external-id-relationship")

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class ExternalIds(BaseModel):
    """The external identifier list of an element."""

    last_modified_date: IntValue | None = Field(
        default=None, alias="last-modified-date"
    )
    external_id: list[ExternalId] = Field(default_factory=list, alias="external-id")

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class OrganizationAddress(BaseModel):
    """The city, region, and two-letter country of an organization."""

    city: SafeStr | None = None
    region: SafeStr | None = None
    country: SafeStr | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class DisambiguatedOrganization(BaseModel):
    """An organization linked to a registry such as FUNDREF, ROR, or GRID."""

    identifier: SafeStr | None = Field(
        default=None, alias="disambiguated-organization-identifier"
    )
    source: SafeStr | None = Field(default=None, alias="disambiguation-source")

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Organization(BaseModel):
    """An organization attached to an affiliation, funding, or peer review."""

    name: SafeStr | None = None
    address: OrganizationAddress | None = None
    disambiguated_organization: DisambiguatedOrganization | None = Field(
        default=None, alias="disambiguated-organization"
    )

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class ContributorAttributes(BaseModel):
    """The role and sequence of one contributor."""

    contributor_role: SafeStr | None = Field(default=None, alias="contributor-role")
    contributor_sequence: SafeStr | None = Field(
        default=None, alias="contributor-sequence"
    )

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Contributor(BaseModel):
    """One contributor of a work or funding entry."""

    orcid: OrcidId | None = Field(default=None, alias="contributor-orcid")
    credit_name: TextValue | None = Field(default=None, alias="credit-name")
    email: TextValue | None = Field(default=None, alias="contributor-email")
    attributes: ContributorAttributes | None = Field(
        default=None, alias="contributor-attributes"
    )

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Contributors(BaseModel):
    """The contributor list of a work or funding entry."""

    contributor: list[Contributor] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Title(BaseModel):
    """The title of a work or funding entry.

    ``subtitle`` exists on works; ``translated_title`` is a wrapper with a
    ``language-code`` alongside its ``value``.
    """

    title: TextValue | None = None
    subtitle: TextValue | None = None
    translated_title: TextValue | None = Field(default=None, alias="translated-title")

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Citation(BaseModel):
    """A formatted citation of a work, as supplied by the source."""

    citation_type: SafeStr | None = Field(default=None, alias="citation-type")
    citation_value: SafeStr | None = Field(default=None, alias="citation-value")

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Amount(BaseModel):
    """A funding amount with its currency code."""

    currency_code: SafeStr | None = Field(default=None, alias="currency-code")
    value: SafeStr | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


__all__ = [
    "Amount",
    "Citation",
    "Contributor",
    "ContributorAttributes",
    "Contributors",
    "DisambiguatedOrganization",
    "ExternalId",
    "ExternalIds",
    "FuzzyDate",
    "IntValue",
    "Organization",
    "OrganizationAddress",
    "OrcidId",
    "Source",
    "TextValue",
    "Title",
]
