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

#: Rate class of the two search routes (see :func:`is_search_route`).
ZENODO_SEARCH_RATE_CLASS = "search"

#: Requests per second that callers without a token get on the search
#: routes: the 31st request in a minute answers 429 ``30 per 1 minute``.
#: Every other route allows 133 per minute (verified 2026-11-28).
ZENODO_SEARCH_REQUESTS_PER_SECOND = 0.5

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


def is_search_route(path: str, api_path: str = "/api") -> bool:
    """Return whether ``path`` is one of the two Zenodo search routes.

    The record search (``/records``) and the search over the records of one
    community (``/communities/{slug}/records``) share the stricter limit of
    the search engine. Every other route, including OAI-PMH, does not.

    Args:
        path: Path of the request URL.
        api_path: Path prefix of the REST API below the host.
    """
    prefix = api_path.rstrip("/")
    if not path.rstrip("/").startswith(f"{prefix}/"):
        return False
    relative = path.rstrip("/")[len(prefix) :]
    return relative == "/records" or relative.endswith("/records")


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
    "ZENODO_SEARCH_RATE_CLASS",
    "ZENODO_SEARCH_REQUESTS_PER_SECOND",
    "dialect_for",
    "is_search_route",
]
