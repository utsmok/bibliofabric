"""ORCID query dialect constants and the search paging rules.

``ORCID_SEARCH_DIALECT`` tells bibliofabric how the ORCID search routes name
their query parameters. The resource-client base that consumes these
constants lives in :mod:`orchis._async.resources` (its sync twin is
generated from it).
"""

from bibliofabric.paging import QueryDialect

#: Base URL of the ORCID Public API v3.0.
ORCID_API_BASE_URL = "https://pub.orcid.org/v3.0"

#: Expanded search answers at most this many results per page; a larger
#: ``rows`` value makes Solr fail with HTTP 500 (verified 2026-11-27 with
#: ``rows=1000``).
EXPANDED_SEARCH_MAX_ROWS = 100

#: Default page size for search routes. The API defaults to 1000 for
#: ``/expanded-search`` and 100 for ``/search``; the client asks for smaller
#: pages so one request stays small.
DEFAULT_SEARCH_ROWS = 50

ORCID_SEARCH_DIALECT = QueryDialect(
    page_size_param="rows",
    max_page_size=EXPANDED_SEARCH_MAX_ROWS,
    default_page_size=DEFAULT_SEARCH_ROWS,
    iterate_page_size=DEFAULT_SEARCH_ROWS,
    count_page_size=1,
    page_param=None,
    offset_param="start",
    page_start=0,
    sort_param=None,
    query_param="q",
    select_param=None,
)

#: Dialect for record-bound routes, which have no listing at all.
ORCID_ITEM_DIALECT = QueryDialect(
    page_size_param=None,
    max_page_size=1,
    default_page_size=1,
    count_page_size=1,
    page_param=None,
    page_start=1,
    sort_param=None,
    query_param=None,
    select_param=None,
)
