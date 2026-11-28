"""Models for the ORCID person section and its sub-sections."""

from bibliofabric import SafeList, SafeStr
from pydantic import BaseModel, ConfigDict, Field

from .common import Source
from .values import IntValue, TextValue


class _Element(BaseModel):
    """Fields every person element carries."""

    created_date: IntValue | None = Field(default=None, alias="created-date")
    last_modified_date: IntValue | None = Field(
        default=None, alias="last-modified-date"
    )
    source: Source | None = None
    visibility: SafeStr | None = None
    path: SafeStr | None = None
    put_code: int | None = Field(default=None, alias="put-code")
    display_index: int | str | None = Field(default=None, alias="display-index")

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Name(_Element):
    """The person's name (``given-names`` and ``family-name``, both singular)."""

    given_names: TextValue | None = Field(default=None, alias="given-names")
    family_name: TextValue | None = Field(default=None, alias="family-name")
    credit_name: TextValue | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class OtherName(_Element):
    """A name variant, stored in ``content`` (not in a ``value`` wrapper)."""

    content: SafeStr | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class OtherNames(BaseModel):
    """The other-names group."""

    last_modified_date: IntValue | None = Field(
        default=None, alias="last-modified-date"
    )
    other_name: SafeList[OtherName] = Field(default_factory=list, alias="other-name")
    path: SafeStr | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Biography(BaseModel):
    """The free-text biography (route answers 404 when the record has none)."""

    last_modified_date: IntValue | None = Field(
        default=None, alias="last-modified-date"
    )
    content: SafeStr | None = None
    visibility: SafeStr | None = None
    path: SafeStr | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class ResearcherUrl(_Element):
    """One link the researcher added to their record."""

    url_name: SafeStr | None = Field(default=None, alias="url-name")
    url: TextValue | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class ResearcherUrls(BaseModel):
    """The researcher-urls group."""

    last_modified_date: IntValue | None = Field(
        default=None, alias="last-modified-date"
    )
    researcher_url: SafeList[ResearcherUrl] = Field(
        default_factory=list, alias="researcher-url"
    )
    path: SafeStr | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Email(_Element):
    """One verified (or unverified) email address."""

    email: SafeStr | None = None
    primary: bool | None = None
    verified: bool | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Emails(BaseModel):
    """The emails group (route answers 404 when the record has none)."""

    last_modified_date: IntValue | None = Field(
        default=None, alias="last-modified-date"
    )
    email: SafeList[Email] = Field(default_factory=list)
    path: SafeStr | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Keyword(_Element):
    """One research keyword, stored in ``content``."""

    content: SafeStr | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Keywords(BaseModel):
    """The keywords group."""

    last_modified_date: IntValue | None = Field(
        default=None, alias="last-modified-date"
    )
    keyword: SafeList[Keyword] = Field(default_factory=list)
    path: SafeStr | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class CountryValue(TextValue):
    """The two-letter ISO country of a person address (a ``value`` wrapper)."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class PersonAddress(_Element):
    """One country address entry of a person record."""

    country: CountryValue | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Addresses(BaseModel):
    """The address group."""

    last_modified_date: IntValue | None = Field(
        default=None, alias="last-modified-date"
    )
    address: SafeList[PersonAddress] = Field(default_factory=list)
    path: SafeStr | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class ExternalIdentifier(_Element):
    """An external identifier of the person (Scopus id, ISNI, and so on)."""

    type: SafeStr | None = Field(default=None, alias="external-id-type")
    value: SafeStr | None = Field(default=None, alias="external-id-value")
    url: TextValue | None = Field(default=None, alias="external-id-url")
    relationship: SafeStr | None = Field(default=None, alias="external-id-relationship")

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class ExternalIdentifiers(BaseModel):
    """The external-identifiers group."""

    last_modified_date: IntValue | None = Field(
        default=None, alias="last-modified-date"
    )
    external_identifier: SafeList[ExternalIdentifier] = Field(
        default_factory=list, alias="external-identifier"
    )
    path: SafeStr | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Person(BaseModel):
    """The full person section of a record."""

    last_modified_date: IntValue | None = Field(
        default=None, alias="last-modified-date"
    )
    name: Name | None = None
    other_names: OtherNames | None = Field(default=None, alias="other-names")
    biography: Biography | None = None
    researcher_urls: ResearcherUrls | None = Field(
        default=None, alias="researcher-urls"
    )
    emails: Emails | None = None
    addresses: Addresses | None = None
    keywords: Keywords | None = None
    external_identifiers: ExternalIdentifiers | None = Field(
        default=None, alias="external-identifiers"
    )
    path: SafeStr | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class PersonalDetails(BaseModel):
    """The personal-details section (name, other names, biography)."""

    last_modified_date: IntValue | None = Field(
        default=None, alias="last-modified-date"
    )
    name: Name | None = None
    other_names: OtherNames | None = Field(default=None, alias="other-names")
    biography: Biography | None = None
    path: SafeStr | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


__all__ = [
    "Addresses",
    "Biography",
    "CountryValue",
    "Email",
    "Emails",
    "ExternalIdentifier",
    "ExternalIdentifiers",
    "Keyword",
    "Keywords",
    "Name",
    "OtherName",
    "OtherNames",
    "Person",
    "PersonAddress",
    "PersonalDetails",
    "ResearcherUrl",
    "ResearcherUrls",
]
