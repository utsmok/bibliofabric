"""Pydantic models for Semantic Scholar papers, authors, and datasets."""

from .author import Author, NormalizedAffiliation
from .dataset import (
    DatasetDiff,
    DatasetDiffList,
    DatasetMetadata,
    DatasetSummary,
    Release,
)
from .paper import (
    AutocompletePaper,
    Citation,
    CitationContext,
    Embedding,
    ExternalIds,
    Journal,
    OpenAccessPdf,
    Paper,
    PaperMatch,
    PublicationVenue,
    Reference,
    S2FieldOfStudy,
    Tldr,
)
from .patent import Patent, PatentCitations
from .snippet import (
    RefMention,
    Sentence,
    Snippet,
    SnippetAnnotations,
    SnippetMatch,
    SnippetPaper,
    SnippetSearchResult,
)

__all__ = [
    "Author",
    "AutocompletePaper",
    "Citation",
    "CitationContext",
    "DatasetDiff",
    "DatasetDiffList",
    "DatasetMetadata",
    "DatasetSummary",
    "Embedding",
    "ExternalIds",
    "Journal",
    "NormalizedAffiliation",
    "OpenAccessPdf",
    "Paper",
    "PaperMatch",
    "Patent",
    "PatentCitations",
    "PublicationVenue",
    "RefMention",
    "Reference",
    "Release",
    "S2FieldOfStudy",
    "Sentence",
    "Snippet",
    "SnippetAnnotations",
    "SnippetMatch",
    "SnippetPaper",
    "SnippetSearchResult",
    "Tldr",
]
