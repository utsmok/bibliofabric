"""ISSN Portal constants.

The portal serves three kinds of read routes: JSON-LD record nodes under
``/resource`` (content negotiation), and two server-rendered HTML routes
(``/search`` and ``/ltwa``) that this package parses. The constants here name
those routes and the query parameters the HTML forms accept.
"""

from bibliofabric.paging import QueryDialect

#: Base URL of the ISSN Portal.
ISSN_PORTAL_BASE_URL = "https://portal.issn.org"

#: Path prefix of the JSON-LD record routes.
RECORD_PATH_PREFIX = "resource"

#: The portal serves JSON-LD only under these route prefixes; other
#: ``/resource`` prefixes (for example ``ISSN-H``) answer HTML only (verified
#: 2026-11-27).
JSON_LD_ROUTES = frozenset({"ISSN", "ISSN-L"})

#: Page sizes the search form offers (2026-11-27).
SEARCH_PAGE_SIZES = (20, 30, 50, 100)

#: ``sort_field`` values the search form offers (2026-11-27). The value for
#: relevance contains a space and travels URL-encoded.
SEARCH_SORT_FIELDS = ("search score", "title", "country", "issn")

#: ``sort_order`` values accepted next to ``sort_field``.
SEARCH_SORT_ORDERS = ("asc", "desc")

#: Values of the ``partner_repositories`` checkboxes (2026-11-27).
PARTNER_REPOSITORIES = frozenset({"kee", "roa", "tra"})

#: Values of the ``category`` filter checkbox seen in search results
#: (``reg`` labels a confirmed record; 2026-11-27).
SEARCH_CATEGORIES = frozenset({"reg"})

#: Default page size of the search result list.
DEFAULT_SEARCH_PAGE_SIZE = 20

#: Sort keys of the Title Word Abbreviation table.
LTWA_SORT_FIELDS = ("word", "abbreviation")

#: Sort orders of the Title Word Abbreviation table.
LTWA_SORT_ORDERS = ("asc", "desc")

#: Default page size of the Title Word Abbreviation table.
DEFAULT_LTWA_PAGE_SIZE = 20

#: The Title Word Abbreviation table answers an empty table for larger page
#: sizes; 100 is the largest value that returns rows (verified 2026-11-27).
MAX_LTWA_PAGE_SIZE = 100

#: Dialect for the single-node JSON-LD record routes, which have no listing.
ISSN_ITEM_DIALECT = QueryDialect(
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

__all__ = [
    "DEFAULT_LTWA_PAGE_SIZE",
    "DEFAULT_SEARCH_PAGE_SIZE",
    "ISSN_ITEM_DIALECT",
    "ISSN_PORTAL_BASE_URL",
    "JSON_LD_ROUTES",
    "LTWA_SORT_FIELDS",
    "LTWA_SORT_ORDERS",
    "MAX_LTWA_PAGE_SIZE",
    "PARTNER_REPOSITORIES",
    "RECORD_PATH_PREFIX",
    "SEARCH_CATEGORIES",
    "SEARCH_PAGE_SIZES",
    "SEARCH_SORT_FIELDS",
    "SEARCH_SORT_ORDERS",
]
