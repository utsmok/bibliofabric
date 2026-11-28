"""Pydantic models for Semantic Scholar snippet search.

Snippets are excerpts of roughly 500 words drawn from a paper's title,
abstract, and body text. A match carries the snippet text, its location
annotations, a relevance score, and a minimal paper record.
"""

from bibliofabric import SafeList, SafeStr
from pydantic import BaseModel, ConfigDict


class Sentence(BaseModel):
    """A sentence span inside the snippet, as character offsets."""

    start: int | None = None
    end: int | None = None

    model_config = ConfigDict(extra="allow")


class RefMention(BaseModel):
    """A reference mention span, with the corpus id of the mentioned paper."""

    start: int | None = None
    end: int | None = None
    matchedPaperCorpusId: int | None = None

    model_config = ConfigDict(extra="allow")


class SnippetAnnotations(BaseModel):
    """The sentence and reference-mention annotations of one snippet."""

    sentences: SafeList[Sentence] = []
    refMentions: SafeList[RefMention] = []

    model_config = ConfigDict(extra="allow")


class Snippet(BaseModel):
    """One text excerpt with its kind, section, and annotations."""

    text: SafeStr | None = None
    snippetKind: SafeStr | None = None
    section: SafeStr | None = None
    snippetOffset: SafeList[int] = []
    annotations: SnippetAnnotations | None = None

    model_config = ConfigDict(extra="allow")


class SnippetPaper(BaseModel):
    """The minimal paper record attached to a snippet match."""

    corpusId: int | None = None
    title: SafeStr | None = None
    authors: SafeList[dict] = []
    openAccessInfo: dict | None = None

    model_config = ConfigDict(extra="allow")


class SnippetMatch(BaseModel):
    """One snippet-search hit."""

    snippet: Snippet | None = None
    score: float | None = None
    paper: SnippetPaper | None = None

    model_config = ConfigDict(extra="allow")


class SnippetSearchResult(BaseModel):
    """The envelope of ``/snippet/search``."""

    data: SafeList[SnippetMatch] = []
    retrievalVersion: int | None = None

    model_config = ConfigDict(extra="allow")


__all__ = [
    "RefMention",
    "Sentence",
    "Snippet",
    "SnippetAnnotations",
    "SnippetMatch",
    "SnippetPaper",
    "SnippetSearchResult",
]
