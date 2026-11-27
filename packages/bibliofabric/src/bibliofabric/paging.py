"""Pagination dialects and the generic page result.

A :class:`QueryDialect` describes how one API expresses paging, sorting, free
text search, and field selection. :class:`Page` is the uniform result of
``ResourceClient.search()``.
"""

from dataclasses import dataclass, field
from typing import Any

from .exceptions import ConfigurationError


@dataclass(frozen=True, slots=True)
class QueryDialect:
    """Declares the query parameter names and paging rules of an API.

    Set a parameter name to ``None`` when the API does not support the
    feature: ``page_param=None`` means the API has no page numbers,
    ``offset_param`` routes paging through an offset instead, and
    ``cursor_param`` enables cursor paging, which takes precedence over page
    and offset paging in ``iterate()``. Set ``cursor_start=None`` for APIs
    whose first cursor request omits the cursor parameter (e.g. token-based
    bulk search).
    """

    page_size_param: str
    max_page_size: int
    default_page_size: int = 25
    iterate_page_size: int | None = None
    """Page size ``iterate()`` uses when the caller passes none; falls back to ``default_page_size``."""
    count_page_size: int = 1
    """Page size ``count()`` requests (e.g. ``0`` for APIs supporting zero-row count queries)."""
    page_param: str | None = "page"
    page_start: int = 1
    offset_param: str | None = None
    cursor_param: str | None = None
    cursor_start: str | None = "*"
    sort_param: str | None = "sort"
    query_param: str | None = None
    select_param: str | None = None

    def __post_init__(self) -> None:
        if self.max_page_size <= 0:
            raise ConfigurationError(
                f"QueryDialect.max_page_size must be positive, got {self.max_page_size}."
            )
        if not 0 < self.default_page_size <= self.max_page_size:
            raise ConfigurationError(
                f"QueryDialect.default_page_size must be between 1 and "
                f"{self.max_page_size}, got {self.default_page_size}."
            )
        if (
            self.iterate_page_size is not None
            and not 0 < self.iterate_page_size <= self.max_page_size
        ):
            raise ConfigurationError(
                f"QueryDialect.iterate_page_size must be between 1 and "
                f"{self.max_page_size}, got {self.iterate_page_size}."
            )
        if not 0 <= self.count_page_size <= self.max_page_size:
            raise ConfigurationError(
                f"QueryDialect.count_page_size must be between 0 and "
                f"{self.max_page_size}, got {self.count_page_size}."
            )


@dataclass(frozen=True, slots=True)
class Page[E]:
    """Uniform result envelope for ``ResourceClient.search()``."""

    results: list[E]
    total: int | None
    next_cursor: str | None
    page: int | None
    meta: dict[str, Any] = field(default_factory=dict)
    """The raw envelope minus the results, for API extras such as facets."""


__all__ = ["Page", "QueryDialect"]
