"""Query dialect and endpoint paths for Wikidata.

All requests go to two hosts. ``www.wikidata.org`` serves both the MediaWiki
Action API (``w/api.php``) and the Wikibase REST API
(``w/rest.php/wikibase/v1``), so one client with one rate limiter covers
both. The SPARQL query service lives on ``query.wikidata.org`` and is served
by a second client instance that shares the settings object and the limiter
through the ``sparql`` rate class.
"""

from bibliofabric.paging import QueryDialect

ACTION_PATH = "w/api.php"
"""Path of the MediaWiki Action API on ``www.wikidata.org``."""

REST_PREFIX = "w/rest.php/wikibase/v1"
"""Path prefix of the Wikibase REST API on ``www.wikidata.org``."""

REST_LEXEME_PREFIX = "w/rest.php/wikibaselexeme/v0"
"""Path prefix of the WikibaseLexeme REST API on ``www.wikidata.org``."""

ACTION_API_BASE_URL = "https://www.wikidata.org"
"""Base URL of the Action API and REST API host."""

SPARQL_BASE_URL = "https://query.wikidata.org"
"""Base URL of the SPARQL query service host."""

SPARQL_PATH = "sparql"
"""Path of the SPARQL endpoint on ``query.wikidata.org``."""

#: Maximum number of ids per ``wbgetentities`` request. The API answers
#: ``toomanyvalues`` above 50 (verified on 2026-11-27).
MAX_IDS_PER_REQUEST = 50

#: Maximum number of results per ``wbsearchentities`` request.
MAX_SEARCH_LIMIT = 50

#: Search pages by ``continue`` (the next offset), ``limit`` results per page.
#: There is no total in the response, no cursor, and no sort or field
#: selection.
WIKIDATA_DIALECT = QueryDialect(
    page_size_param="limit",
    max_page_size=MAX_SEARCH_LIMIT,
    default_page_size=MAX_SEARCH_LIMIT,
    iterate_page_size=MAX_SEARCH_LIMIT,
    count_page_size=1,
    page_param=None,
    offset_param="continue",
    cursor_param=None,
    sort_param=None,
    query_param="search",
    select_param=None,
)


__all__ = [
    "ACTION_API_BASE_URL",
    "ACTION_PATH",
    "MAX_IDS_PER_REQUEST",
    "MAX_SEARCH_LIMIT",
    "REST_LEXEME_PREFIX",
    "REST_PREFIX",
    "SPARQL_BASE_URL",
    "SPARQL_PATH",
    "WIKIDATA_DIALECT",
]
