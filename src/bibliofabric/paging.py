"""Pagination dialects and the generic page result.

A :class:`QueryDialect` describes how one API expresses paging, sorting, free
text search, and field selection. :class:`Page` is the uniform result of
``ResourceClient.search()``.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class QueryDialect:
    """Declares the query parameter names and paging rules of an API.

    Set a parameter name to ``None`` when the API does not support the
    feature: ``page_param=None`` means the API has no page numbers,
    ``offset_param`` routes paging through an offset instead, and
    ``cursor_param`` enables cursor paging, which takes precedence over page
    and offset paging in ``iterate()``.
    """

    page_size_param: str
    max_page_size: int
    default_page_size: int = 25
    page_param: str | None = "page"
    page_start: int = 1
    offset_param: str | None = None
    cursor_param: str | None = None
    cursor_start: str = "*"
    sort_param: str | None = "sort"
    query_param: str | None = None
    select_param: str | None = None


@dataclass(frozen=True, slots=True)
class Page[E]:
    """Uniform result envelope for ``ResourceClient.search()``."""

    results: list[E]
    total: int | None
    next_cursor: str | None
    page: int | None
    meta: dict[str, Any] = field(default_factory=dict)
    """The raw envelope minus the results, for API extras such as facets."""
