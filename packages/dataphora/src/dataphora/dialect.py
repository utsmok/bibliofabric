"""DataCite query dialect constants.

``DATACITE_DIALECT`` tells bibliofabric how DataCite names its query
parameters. The resource-client base that consumes these constants lives in
:mod:`dataphora._async.dialect` (its sync twin is generated from it).

Verified against the live API and the DataCite documentation on 2026-11-27:

- The default page size is 25; ``page[size]`` accepts 0 to 1000.
- Numbered paging (``page[number]``) can reach the first 10,000 records of a
  query only; ``page[cursor]`` paging has no depth limit and always walks in
  ``created`` ascending order.
"""

from dataclasses import replace

from bibliofabric.paging import QueryDialect

#: Base URL of the DataCite REST API.
DATACITE_API_BASE_URL = "https://api.datacite.org"

#: Default records per page (DataCite default).
DATACITE_PAGE_SIZE = 25

#: Maximum ``page[size]``; larger values are clamped to this by the API.
DATACITE_MAX_PAGE_SIZE = 1000

#: Page size ``iterate()`` uses; cursor paging has no record limit, so the
#: client walks as few pages as possible.
DATACITE_ITERATE_PAGE_SIZE = 1000

#: Numbered paging can reach at most this many records of one query.
DATACITE_MAX_NUMBERED_RESULTS = 10000

#: Sort options the ``sort`` parameter accepts (``-`` prefix flips to
#: descending). ``relevance`` needs a ``query``; ``publicationYear`` is not a
#: sort option and is silently ignored by the API.
DATACITE_SORT_OPTIONS = frozenset(
    {
        "relevance",
        "name",
        "-name",
        "created",
        "-created",
        "updated",
        "-updated",
        "published",
        "-published",
        "view-count",
        "-view-count",
        "download-count",
        "-download-count",
        "citation-count",
        "-citation-count",
        "title",
        "-title",
    }
)

DATACITE_DIALECT = QueryDialect(
    page_size_param="page[size]",
    max_page_size=DATACITE_MAX_PAGE_SIZE,
    default_page_size=DATACITE_PAGE_SIZE,
    iterate_page_size=DATACITE_ITERATE_PAGE_SIZE,
    count_page_size=1,
    page_param="page[number]",
    page_start=1,
    cursor_param="page[cursor]",
    cursor_start="1",
    sort_param="sort",
    query_param="query",
    select_param="fields[dois]",
)


def dialect_with(select_param: str | None) -> QueryDialect:
    """Return ``DATACITE_DIALECT`` with another sparse-fieldset parameter.

    Each resource family names its own field-selection parameter
    (``fields[dois]``, ``fields[clients]``), so every resource client derives
    its dialect from the shared one.
    """
    return replace(DATACITE_DIALECT, select_param=select_param)


__all__ = [
    "DATACITE_API_BASE_URL",
    "DATACITE_DIALECT",
    "DATACITE_ITERATE_PAGE_SIZE",
    "DATACITE_MAX_NUMBERED_RESULTS",
    "DATACITE_MAX_PAGE_SIZE",
    "DATACITE_PAGE_SIZE",
    "DATACITE_SORT_OPTIONS",
    "dialect_with",
]
