"""Query dialects for the OpenAIRE Graph and Scholexplorer APIs."""

from bibliofabric.paging import QueryDialect

GRAPH_DIALECT = QueryDialect(
    page_size_param="page_size",
    max_page_size=10000,
    default_page_size=25,
    iterate_page_size=100,
    page_param="page",
    page_start=1,
    cursor_param="cursor",
    cursor_start="*",
    sort_param="sort",
    query_param="search",
    select_param="select",
)
"""V4 filter-based entity endpoints: ``page`` is 1-indexed, ``page_size`` goes
up to 10000, ``iterate()`` fetches 100 records per page by default, and cursor
paging has no depth cap."""

LINKS_DIALECT = QueryDialect(
    page_size_param="pageSize",
    max_page_size=99,
    default_page_size=99,
    page_param="page",
    page_start=0,
    cursor_param=None,
    sort_param=None,
    query_param=None,
    select_param=None,
)
"""``/v3/research-products/links``: 0-indexed pages, no cursor. Sizes of 100
or more silently return 10 results (OA-10), so the cap is 99."""

SCHOLIX_DIALECT = QueryDialect(
    page_size_param="size",
    max_page_size=99,
    default_page_size=99,
    page_param="page",
    page_start=0,
    cursor_param=None,
    sort_param=None,
    query_param=None,
    select_param=None,
)
"""Scholexplorer ``Links`` endpoints: 0-indexed pages, ``size`` capped at 99
for the same silent-truncation reason."""
