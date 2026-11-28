"""Zenodo query dialect constants.

``ZENODO_DIALECT`` tells bibliofabric how Zenodo names its query parameters.
The resource-client base that consumes these constants lives in
:mod:`zenotheca._async.dialect` (its sync twin is generated from it).
"""

from bibliofabric.paging import QueryDialect

#: Base URL of the Zenodo REST API.
ZENODO_API_BASE_URL = "https://zenodo.org/api"

#: OAI-PMH endpoint of the same repository (not wrapped by this client).
ZENODO_OAI_BASE_URL = "https://zenodo.org/oai2d"

#: Largest ``size`` the API accepts without an access token (verified
#: 2026-11-27; larger values answer HTTP 400). Authenticated callers may
#: raise it to 100.
ZENODO_MAX_PAGE_SIZE = 25

#: Largest ``size`` for token holders, as documented upstream (not
#: verified live; no token was available on 2026-11-27).
ZENODO_MAX_AUTH_PAGE_SIZE = 100

#: Default ``size`` Zenodo answers without a ``size`` parameter.
ZENODO_DEFAULT_PAGE_SIZE = 25

#: Elasticsearch ``index.max_result_window``; a request whose
#: ``page * size`` exceeds it answers HTTP 400 (verified 2026-11-27).
ZENODO_MAX_RESULT_WINDOW = 10_000

#: Sort options the records search accepts (verified 2026-11-27).
RECORD_SORT_OPTIONS = frozenset({"bestmatch", "mostrecent", "-mostrecent"})

ZENODO_DIALECT = QueryDialect(
    page_size_param="size",
    max_page_size=ZENODO_MAX_PAGE_SIZE,
    default_page_size=ZENODO_DEFAULT_PAGE_SIZE,
    iterate_page_size=ZENODO_MAX_PAGE_SIZE,
    count_page_size=1,
    page_param="page",
    page_start=1,
    max_offset=ZENODO_MAX_RESULT_WINDOW - 1,
    sort_param="sort",
    query_param="q",
    select_param=None,
)

#: The dialect for callers with an access token; Zenodo documents a page
#: size of 100 for them (not verified live; no token exists in CI).
ZENODO_DIALECT_AUTHED = QueryDialect(
    page_size_param="size",
    max_page_size=ZENODO_MAX_AUTH_PAGE_SIZE,
    default_page_size=ZENODO_DEFAULT_PAGE_SIZE,
    iterate_page_size=ZENODO_MAX_AUTH_PAGE_SIZE,
    count_page_size=1,
    page_param="page",
    page_start=1,
    max_offset=ZENODO_MAX_RESULT_WINDOW - 1,
    sort_param="sort",
    query_param="q",
    select_param=None,
)


def dialect_for(api_token: str | None) -> QueryDialect:
    """Return the query dialect for a caller with or without a token.

    Without a token the page size caps at 25 (verified 2026-11-27); with a
    token the client allows the documented 100.
    """
    return ZENODO_DIALECT_AUTHED if api_token else ZENODO_DIALECT


__all__ = [
    "RECORD_SORT_OPTIONS",
    "ZENODO_API_BASE_URL",
    "ZENODO_DIALECT",
    "ZENODO_DIALECT_AUTHED",
    "ZENODO_DEFAULT_PAGE_SIZE",
    "ZENODO_MAX_AUTH_PAGE_SIZE",
    "ZENODO_MAX_PAGE_SIZE",
    "ZENODO_MAX_RESULT_WINDOW",
    "ZENODO_OAI_BASE_URL",
    "dialect_for",
]
