"""Crossref query dialect: constants and pure helpers shared by both variants.

``CrossrefDialect`` declares how Crossref expresses paging, sorting, search,
and field selection. The resource-client base that applies it lives in
:mod:`stavrophora._async.dialect` (async) and its generated sync twin
:mod:`stavrophora._sync.dialect`; both import the constants and helpers
defined here. Conventions:

- one ``filter=key:value,...`` parameter (repeated keys OR, distinct keys AND)
- ``sort`` split into ``sort=<field>&order=<asc|desc>`` from ``field:desc``
- works-only parameters (``sort``, ``select``, filters) rejected client-side
  on routes that do not accept them
- ``offset + rows <= 10000`` enforced before the request
- cursor iteration rejected for date sorts the API no longer allows
"""

from collections.abc import Mapping, Sequence
from typing import Any

from bibliofabric.exceptions import ConfigurationError
from bibliofabric.paging import QueryDialect

#: Valid Crossref sort directions.
VALID_SORT_ORDERS = frozenset({"asc", "desc"})

#: Crossref rejects cursor requests that sort by publication dates with a
#: ``sort-criteria-incompatible-with-cursor`` 400 (since 2026-08-24).
CURSOR_INCOMPATIBLE_SORTS = frozenset(
    {"issued", "published", "published-print", "published-online"}
)

#: Crossref rejects offset requests with ``offset + rows > 10000``.
MAX_OFFSET_WINDOW = 10_000

#: Page size used by ``iterate()`` (Crossref caps ``rows`` at 1000).
ITERATE_PAGE_SIZE = 1000

#: Works dialect: supports cursor deep paging and zero-row count queries.
CrossrefDialect = QueryDialect(
    page_size_param="rows",
    max_page_size=1000,
    default_page_size=20,
    iterate_page_size=ITERATE_PAGE_SIZE,
    count_page_size=0,
    page_param=None,
    offset_param="offset",
    max_offset=MAX_OFFSET_WINDOW,
    cursor_param="cursor",
    cursor_start="*",
    sort_param="sort",
    query_param="query",
    select_param="select",
)

#: Non-works dialect: offset-only paging (Crossref rejects ``cursor=*``,
#: ``sort``, and ``select`` on ``/journals``, ``/funders``, ``/members``, and
#: ``/licenses``).
CrossrefOffsetDialect = QueryDialect(
    page_size_param="rows",
    max_page_size=1000,
    default_page_size=20,
    iterate_page_size=ITERATE_PAGE_SIZE,
    count_page_size=0,
    page_param=None,
    offset_param="offset",
    max_offset=MAX_OFFSET_WINDOW,
    cursor_param=None,
    cursor_start=None,
    sort_param=None,
    query_param="query",
    select_param=None,
)

#: Unpaged dialect: ``/types`` ignores paging parameters and rejects
#: ``query``, ``sort``, and ``select``.
CrossrefUnpagedDialect = QueryDialect(
    page_size_param=None,
    max_page_size=1000,
    default_page_size=20,
    iterate_page_size=ITERATE_PAGE_SIZE,
    count_page_size=0,
    page_param=None,
    offset_param=None,
    cursor_param=None,
    cursor_start=None,
    sort_param=None,
    query_param=None,
    select_param=None,
)


def _split_sort(sort: str | Sequence[str]) -> tuple[str, str | None]:
    """Split a sort request into ``(field, order)``.

    Accepts ``"field"``, ``"field:asc"``, or ``"field:desc"``. Crossref takes
    a single sort field, so sequences must hold exactly one entry.
    """
    if isinstance(sort, str):
        field, sep, order = sort.strip().partition(":")
        field = field.strip()
        if not field:
            raise ConfigurationError("Crossref sort field must be non-empty.")
        normalized_order = order.strip().lower() or None
        if sep and normalized_order not in VALID_SORT_ORDERS:
            raise ConfigurationError(
                f"Crossref sort order must be 'asc' or 'desc', got {order.strip()!r}."
            )
        return field, normalized_order
    if len(sort) != 1:
        raise ConfigurationError(
            f"Crossref accepts a single sort field, got {len(sort)}: {list(sort)!r}."
        )
    return _split_sort(sort[0])


def _format_filter_value(value: Any) -> str:
    """Render a filter value; booleans lowercase like Crossref expects."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _serialize_filters(filters: Mapping[str, Any]) -> str:
    """Join filter criteria into Crossref's single ``filter`` parameter.

    List values repeat the key (``doi:a,doi:b`` is the OR form; the pipe
    form returns zero results). Distinct keys AND together; ``None`` entries
    are skipped.
    """
    parts: list[str] = []
    for key, value in filters.items():
        if value is None:
            continue
        if isinstance(value, Mapping):
            raise ConfigurationError(f"Filter {key!r} must be a scalar or a list.")
        values = (
            list(value)
            if isinstance(value, Sequence | set) and not isinstance(value, str | bytes)
            else [value]
        )
        parts.extend(
            f"{key}:{_format_filter_value(item)}" for item in values if item is not None
        )
    return ",".join(parts)
