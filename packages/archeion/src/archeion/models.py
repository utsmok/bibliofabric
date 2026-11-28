"""Pydantic models for arXiv query API entries.

The models validate the dicts that :func:`archeion.atom.parse_feed` builds
from the Atom feed. Every field is optional and ``extra="allow"`` keeps any
field a later parser version adds.
"""

import re

from bibliofabric import SafeList, SafeStr
from pydantic import BaseModel, ConfigDict

#: The trailing version of an arXiv id (``v7`` in ``1706.03762v7``).
_VERSION = re.compile(r"v(\d+)$")


class ArxivAuthor(BaseModel):
    """One author of an entry with the affiliations arXiv knows."""

    name: SafeStr | None = None
    affiliations: SafeList[str] = []

    model_config = ConfigDict(extra="allow")


class ArxivLink(BaseModel):
    """One ``link`` element: the abstract page, the PDF, or the DOI."""

    href: SafeStr | None = None
    rel: SafeStr | None = None
    type: SafeStr | None = None
    title: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class ArxivEntry(BaseModel):
    """One paper version from the arXiv query API.

    ``id`` is the abstract URL of the version the feed returned
    (``http://arxiv.org/abs/1706.03762v7``); :attr:`arxiv_id` and
    :attr:`version` split it. ``published`` is the date of version 1 and
    ``updated`` the date of this version.
    """

    id: SafeStr | None = None
    title: SafeStr | None = None
    summary: SafeStr | None = None
    published: SafeStr | None = None
    updated: SafeStr | None = None
    authors: SafeList[ArxivAuthor] = []
    links: SafeList[ArxivLink] = []
    categories: SafeList[str] = []
    primary_category: SafeStr | None = None
    comment: SafeStr | None = None
    journal_ref: SafeStr | None = None
    doi: SafeStr | None = None

    model_config = ConfigDict(extra="allow")

    @property
    def versioned_id(self) -> str | None:
        """The id with its version, such as ``1706.03762v7``."""
        if not self.id:
            return None
        return self.id.split("/abs/", 1)[-1]

    @property
    def arxiv_id(self) -> str | None:
        """The id without its version, such as ``1706.03762``."""
        versioned = self.versioned_id
        return _VERSION.sub("", versioned) if versioned else None

    @property
    def version(self) -> int | None:
        """The version number, such as ``7``."""
        versioned = self.versioned_id
        match = _VERSION.search(versioned) if versioned else None
        return int(match.group(1)) if match else None

    @property
    def pdf_url(self) -> str | None:
        """The URL of the PDF of this version."""
        for link in self.links:
            if link.title == "pdf" or link.type == "application/pdf":
                return link.href
        return None

    @property
    def author_names(self) -> list[str]:
        """The author names in feed order."""
        return [author.name for author in self.authors if author.name]


__all__ = ["ArxivAuthor", "ArxivEntry", "ArxivLink"]
