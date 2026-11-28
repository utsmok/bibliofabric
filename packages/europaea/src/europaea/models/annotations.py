"""Pydantic models for the Europe PMC annotations API."""

from pydantic import BaseModel, ConfigDict, Field


class AnnotationTag(BaseModel):
    """One ontology tag attached to an annotation (``tags``)."""

    model_config = ConfigDict(extra="allow")

    name: str | None = None
    uri: str | None = None


class Annotation(BaseModel):
    """One annotation of an article: a text span plus its ontology tags."""

    model_config = ConfigDict(extra="allow")

    prefix: str | None = None
    exact: str | None = None
    postfix: str | None = None
    tags: list[AnnotationTag] | None = None
    id: str | None = None
    type: str | None = None
    sub_type: str | None = Field(None, alias="subType")
    section: str | None = None
    provider: str | None = None
    frequency: int | None = None


class ArticleAnnotations(BaseModel):
    """The annotations of one article (one element of the answer list)."""

    model_config = ConfigDict(extra="allow")

    source: str | None = None
    ext_id: str | None = Field(None, alias="extId")
    pmcid: str | None = None
    annotations: list[Annotation] | None = None


class AnnotationPage(BaseModel):
    """One page of a cursor-paged annotations query.

    ``by_entity``, ``by_provider``, ``by_relationship`` and ``by_section``
    answer this shape; ``next_cursor_mark`` is the cursor to pass back. The
    API signals exhaustion with ``-1.0``, which the client maps to ``None``.
    """

    model_config = ConfigDict(extra="allow")

    cursor_mark: float | None = Field(None, alias="cursorMark")
    next_cursor_mark: float | None = Field(None, alias="nextCursorMark")
    articles: list[ArticleAnnotations] | None = None


__all__ = [
    "Annotation",
    "AnnotationPage",
    "AnnotationTag",
    "ArticleAnnotations",
]
