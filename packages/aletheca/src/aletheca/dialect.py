"""OpenAlex query dialect constants.

``OPENALEX_DIALECT`` tells bibliofabric how OpenAlex names its query
parameters. The resource-client base that consumes these constants lives in
:mod:`aletheca._async.dialect` (its sync twin is generated from it).
"""

from bibliofabric.paging import QueryDialect

#: Base URL of the OpenAlex API.
OPENALEX_API_BASE_URL = "https://api.openalex.org"

#: OpenAlex caps pipe-joined OR lists at 100 values per filter.
MAX_OR_VALUES = 100

#: OpenAlex caps basic page-number paging at ``page * per_page <= 10,000``.
MAX_BASIC_PAGING_RESULTS = 10_000

#: Entity routes supported by ``/autocomplete/{entity_type}``.
AUTOCOMPLETE_ENTITY_TYPES = frozenset(
    {
        "works",
        "authors",
        "sources",
        "institutions",
        "topics",
        "keywords",
        "concepts",
        "publishers",
        "funders",
    }
)

OPENALEX_DIALECT = QueryDialect(
    page_size_param="per_page",
    max_page_size=100,
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

_OPENALEX_URL_PREFIX = "https://openalex.org/"
