"""DOAJ query dialect constants.

``DOAJ_DIALECT`` tells bibliofabric how DOAJ names its query parameters. The
resource-client base that consumes these constants lives in
:mod:`diurnalia._async.base` (its sync twin is generated from it).
"""

from bibliofabric.paging import QueryDialect

#: Base URL of the DOAJ API version 4.
DOAJ_API_BASE_URL = "https://doaj.org/api/v4"

#: Public CSV export of every DOAJ journal. The route redirects to a file on
#: Amazon S3 that DOAJ regenerates (about 26 MB and 52 columns on
#: 2026-11-28). The full journal and article data dumps need an access
#: grant from DOAJ and answer 401 otherwise.
DOAJ_JOURNAL_CSV_URL = "https://doaj.org/csv"

#: The API silently clamps ``pageSize`` to this value (verified 2026-11-27).
DOAJ_MAX_PAGE_SIZE = 50

#: ``pageSize`` default of the API when the parameter is missing.
DOAJ_DEFAULT_PAGE_SIZE = 10

#: Largest ``pageSize`` one iteration requests. The API clamps larger values
#: to :data:`DOAJ_MAX_PAGE_SIZE`, so asking for more only wastes bytes.
DOAJ_ITERATE_PAGE_SIZE = 50

#: Largest offset of a query. The API answers
#: ``(page - 1) * pageSize + pageSize <= 1000`` and rejects anything beyond
#: with HTTP 400 ("You cannot access results beyond 1000 records"), so the
#: last record a query can reach is number 1000 (verified 2026-11-27).
DOAJ_MAX_OFFSET = 999

DOAJ_DIALECT = QueryDialect(
    page_size_param="pageSize",
    max_page_size=DOAJ_MAX_PAGE_SIZE,
    default_page_size=DOAJ_DEFAULT_PAGE_SIZE,
    iterate_page_size=DOAJ_ITERATE_PAGE_SIZE,
    count_page_size=1,
    page_param="page",
    page_start=1,
    max_offset=DOAJ_MAX_OFFSET,
    sort_param="sort",
    query_param=None,
    select_param=None,
)

__all__ = [
    "DOAJ_API_BASE_URL",
    "DOAJ_DEFAULT_PAGE_SIZE",
    "DOAJ_DIALECT",
    "DOAJ_ITERATE_PAGE_SIZE",
    "DOAJ_MAX_OFFSET",
    "DOAJ_MAX_PAGE_SIZE",
]
