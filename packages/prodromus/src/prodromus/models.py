"""Pydantic models for the bioRxiv and medRxiv API answers.

Every field is optional and ``extra="allow"`` keeps fields the API adds.
The API sends numbers as strings in places (``version``, ``total``), and
``"NA"`` where a value is missing; the models keep the raw values and the
properties read them.
"""

from bibliofabric import SafeList, SafeStr
from pydantic import BaseModel, ConfigDict, Field


def _split_authors(value: str | None) -> list[str]:
    return [name.strip() for name in (value or "").split(";") if name.strip()]


def _missing(value: str | None) -> str | None:
    return None if value in (None, "", "NA") else value


class FunderDeclaration(BaseModel):
    """One funding declaration of a preprint (``funder`` route only)."""

    name: SafeStr | None = None
    id: SafeStr | None = None
    id_type: SafeStr | None = Field(default=None, alias="id-type")
    award: SafeStr | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Preprint(BaseModel):
    """One version of a bioRxiv or medRxiv preprint.

    ``authors`` is one string with ``;`` between the names, as the API sends
    it; :attr:`author_list` splits it. ``published`` is the DOI of the
    journal article, or ``"NA"``; :attr:`published_doi` reads it.
    """

    doi: SafeStr | None = None
    title: SafeStr | None = None
    authors: SafeStr | None = None
    author_corresponding: SafeStr | None = None
    author_corresponding_institution: SafeStr | None = None
    date: SafeStr | None = None
    version: SafeStr | None = None
    type: SafeStr | None = None
    license: SafeStr | None = None
    category: SafeStr | None = None
    jatsxml: SafeStr | None = None
    abstract: SafeStr | None = None
    published: SafeStr | None = None
    server: SafeStr | None = None
    funder: SafeList[FunderDeclaration] = []

    model_config = ConfigDict(extra="allow")

    @property
    def author_list(self) -> list[str]:
        """The author names in order."""
        return _split_authors(self.authors)

    @property
    def published_doi(self) -> str | None:
        """The DOI of the journal article, or ``None``."""
        return _missing(self.published)

    @property
    def version_number(self) -> int | None:
        """The version as an integer."""
        return int(self.version) if self.version and self.version.isdigit() else None


class PublishedArticle(BaseModel):
    """A preprint and the journal article it became.

    The ``pubs`` route names the preprint DOI ``preprint_doi``; the ``pub``
    and ``publisher`` routes name it ``biorxiv_doi``. :attr:`preprint` reads
    whichever is set.
    """

    preprint_doi: SafeStr | None = None
    biorxiv_doi: SafeStr | None = None
    published_doi: SafeStr | None = None
    published_journal: SafeStr | None = None
    preprint_platform: SafeStr | None = None
    preprint_title: SafeStr | None = None
    preprint_authors: SafeStr | None = None
    preprint_category: SafeStr | None = None
    preprint_date: SafeStr | None = None
    published_date: SafeStr | None = None
    preprint_abstract: SafeStr | None = None
    preprint_author_corresponding: SafeStr | None = None
    preprint_author_corresponding_institution: SafeStr | None = None

    model_config = ConfigDict(extra="allow")

    @property
    def preprint(self) -> str | None:
        """The preprint DOI, from ``preprint_doi`` or ``biorxiv_doi``."""
        return self.preprint_doi or self.biorxiv_doi

    @property
    def author_list(self) -> list[str]:
        """The preprint author names in order."""
        return _split_authors(self.preprint_authors)


class ContentStatistic(BaseModel):
    """New and revised papers per month or year (``sum`` route)."""

    month: SafeStr | None = None
    year: int | str | None = None
    new_papers: int | None = None
    new_papers_cumulative: int | None = None
    revised_papers: int | None = None
    revised_papers_cumulative: int | None = None

    model_config = ConfigDict(extra="allow")


class UsageStatistic(BaseModel):
    """Views and downloads per month or year (``usage`` route)."""

    month: SafeStr | None = None
    year: int | str | None = None
    abstract_views: int | None = None
    full_text_views: int | None = None
    pdf_downloads: int | None = None
    abstract_cumulative: int | None = None
    full_text_cumulative: int | None = None
    pdf_cumulative: int | None = None

    model_config = ConfigDict(extra="allow")


__all__ = [
    "ContentStatistic",
    "FunderDeclaration",
    "Preprint",
    "PublishedArticle",
    "UsageStatistic",
]
