"""Pydantic models for Semantic Scholar authors."""

from typing import TYPE_CHECKING

from bibliofabric import SafeList, SafeStr
from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from .paper import Paper

# The parent module rebuilds Author.papers' forward reference once Paper exists.


class Author(BaseModel):
    """A Semantic Scholar author record.

    Like papers, authors answer ``authorId`` (plus ``name`` on search
    routes) even without ``fields``; every other field appears only when
    the caller asks for it. ``papers`` (on the author record) and
    ``externalIds`` are key-gated upstream: keyless requests that ask for
    them answer HTTP 400.
    """

    authorId: SafeStr | None = None
    externalIds: dict | None = None
    url: SafeStr | None = None
    name: SafeStr | None = None
    aliases: SafeList[str] = []
    affiliations: SafeList[str] = []
    homepage: SafeStr | None = None
    paperCount: int | None = None
    citationCount: int | None = None
    hIndex: int | None = None
    papers: SafeList["Paper"] = []

    model_config = ConfigDict(extra="allow")


__all__ = ["Author"]
