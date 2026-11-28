"""Pydantic models for DOAJ journal records.

The fields mirror the ``bibjson`` block of the v4 search results and the
`/api/v4/journals/{id}` records. Every model allows extra fields, so DOAJ
keeps serving records when it adds a field.
"""

from bibliofabric import SafeList, SafeStr
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from .common import Admin, Subject


class JournalPublisher(BaseModel):
    """The publisher block of a journal."""

    name: SafeStr | None = None
    country: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class License(BaseModel):
    """One license of a journal.

    ``type`` is a Creative Commons name such as ``CC BY`` or ``CC BY-NC``.
    The flag fields carry which license elements apply (``BY``, ``NC``,
    ``ND``, ``SA``).
    """

    type: SafeStr | None = None
    url: SafeStr | None = None
    by: bool | None = Field(None, validation_alias=AliasChoices("by", "BY"))
    nc: bool | None = Field(None, validation_alias=AliasChoices("nc", "NC"))
    nd: bool | None = Field(None, validation_alias=AliasChoices("nd", "ND"))
    sa: bool | None = Field(None, validation_alias=AliasChoices("sa", "SA"))

    model_config = ConfigDict(extra="allow")


class Price(BaseModel):
    """One price of the APC maximum list (amount and currency)."""

    price: float | None = None
    currency: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class Apc(BaseModel):
    """The article processing charge policy of a journal."""

    has_apc: bool | None = None
    max: SafeList[Price] = []
    url: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class OtherCharges(BaseModel):
    """Charges other than the APC (submission fees, page charges)."""

    has_other_charges: bool | None = None
    url: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class Waiver(BaseModel):
    """The fee waiver policy of a journal."""

    has_waiver: bool | None = None
    url: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class Editorial(BaseModel):
    """Peer review and editorial board information."""

    review_process: SafeList[str] = []
    review_url: SafeStr | None = None
    board_url: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class PidScheme(BaseModel):
    """Which persistent identifier schemes the journal participates in."""

    has_pid_scheme: bool | None = None
    scheme: SafeList[str] = []

    model_config = ConfigDict(extra="allow")


class Copyright(BaseModel):
    """The copyright policy of a journal."""

    author_retains: bool | None = None
    url: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class Plagiarism(BaseModel):
    """The plagiarism screening policy of a journal."""

    detection: bool | None = None
    url: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class Preservation(BaseModel):
    """The digital preservation arrangements of a journal."""

    has_preservation: bool | None = None
    service: SafeList[str] = []
    url: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class DepositPolicy(BaseModel):
    """Which deposit policies the journal supports."""

    has_policy: bool | None = None
    service: SafeList[str] = []
    url: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class ArticleDisplay(BaseModel):
    """How article licenses are shown on the journal site."""

    license_display: SafeList[str] = []
    license_display_example_url: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class Ref(BaseModel):
    """Journal website links (aims and scope, OA statement, instructions)."""

    aims_scope: SafeStr | None = None
    journal: SafeStr | None = None
    oa_statement: SafeStr | None = None
    author_instructions: SafeStr | None = None
    license_terms: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class JournalBibjson(BaseModel):
    """The journal metadata of a DOAJ record."""

    title: SafeStr | None = None
    alternative_title: SafeStr | None = None
    publisher: JournalPublisher | None = None
    license: SafeList[License] = []
    pissn: SafeStr | None = None
    eissn: SafeStr | None = None
    language: SafeList[str] = []
    subject: SafeList[Subject] = []
    keywords: SafeList[str] = []
    oa_start: int | None = None
    publication_time_weeks: int | None = None
    boai: bool | None = None
    editorial: Editorial | None = None
    pid_scheme: PidScheme | None = None
    copyright: Copyright | None = None
    plagiarism: Plagiarism | None = None
    preservation: Preservation | None = None
    deposit_policy: DepositPolicy | None = None
    article: ArticleDisplay | None = None
    apc: Apc | None = None
    other_charges: OtherCharges | None = None
    waiver: Waiver | None = None
    ref: Ref | None = None

    model_config = ConfigDict(extra="allow")


class Journal(BaseModel):
    """A DOAJ journal record (search result or `/journals/{id}`)."""

    id: SafeStr | None = None
    bibjson: JournalBibjson
    admin: Admin | None = None
    created_date: SafeStr | None = None
    last_updated: SafeStr | None = None
    last_manual_update: SafeStr | None = None
    es_type: SafeStr | None = None

    model_config = ConfigDict(extra="allow")

    @property
    def title(self) -> str | None:
        """The journal title."""
        return self.bibjson.title

    @property
    def issns(self) -> list[str]:
        """The print and electronic ISSNs that are set."""
        return [issn for issn in (self.bibjson.pissn, self.bibjson.eissn) if issn]

    @property
    def publisher_name(self) -> str | None:
        """The publisher name, or ``None`` when the record has no publisher."""
        return self.bibjson.publisher.name if self.bibjson.publisher else None
