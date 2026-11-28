"""Pydantic models for DOAJ article records.

The fields mirror the ``bibjson`` block of the v4 article search results.
Every model allows extra fields, so DOAJ keeps serving articles when it
adds a field.
"""

from bibliofabric import SafeList, SafeStr
from pydantic import BaseModel, ConfigDict

from .common import Admin, Subject


class Identifier(BaseModel):
    """One identifier of an article (``type`` is ``doi`` or ``eissn``/``pissn``)."""

    id: SafeStr | None = None
    type: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class Author(BaseModel):
    """One author of an article."""

    name: SafeStr | None = None
    affiliation: SafeStr | None = None
    orcid: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class Link(BaseModel):
    """One link of an article.

    ``type`` is ``fulltext`` or ``abstract``; ``content_type`` is ``PDF``,
    ``HTML``, ``ePUB``, or ``XML``.
    """

    type: SafeStr | None = None
    url: SafeStr | None = None
    content_type: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class ArticleJournal(BaseModel):
    """The journal block inside an article record.

    Unlike a journal record, the publisher is a plain name string and the
    ISSNs live in the ``issns`` list.
    """

    title: SafeStr | None = None
    publisher: SafeStr | None = None
    country: SafeStr | None = None
    language: SafeList[str] = []
    issns: SafeList[str] = []
    volume: SafeStr | None = None
    number: SafeStr | None = None
    start: SafeStr | None = None
    end: SafeStr | None = None
    license: SafeList[str] = []
    url: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class ArticleBibjson(BaseModel):
    """The article metadata of a DOAJ record."""

    title: SafeStr | None = None
    abstract: SafeStr | None = None
    author: SafeList[Author] = []
    identifier: SafeList[Identifier] = []
    journal: ArticleJournal | None = None
    link: SafeList[Link] = []
    year: SafeStr | None = None
    month: SafeStr | None = None
    keywords: SafeList[str] = []
    subject: SafeList[Subject] = []

    model_config = ConfigDict(extra="allow")


class Article(BaseModel):
    """A DOAJ article record (search result or `/articles/{id}`)."""

    id: SafeStr | None = None
    bibjson: ArticleBibjson
    admin: Admin | None = None
    created_date: SafeStr | None = None
    last_updated: SafeStr | None = None
    es_type: SafeStr | None = None

    model_config = ConfigDict(extra="allow")

    @property
    def title(self) -> str | None:
        """The article title."""
        return self.bibjson.title

    @property
    def doi(self) -> str | None:
        """The DOI of the article, or ``None`` when the record has none."""
        for identifier in self.bibjson.identifier:
            if identifier.type == "doi" and identifier.id:
                return identifier.id
        return None

    @property
    def issns(self) -> list[str]:
        """The ISSNs of the journal that published the article."""
        return list(self.bibjson.journal.issns) if self.bibjson.journal else []


__all__ = [
    "Article",
    "ArticleBibjson",
    "ArticleJournal",
    "Author",
    "Identifier",
    "Link",
]
