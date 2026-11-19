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

OPENALEX_DIALECT = QueryDialect(
    page_size_param="per-page",
    max_page_size=100,
    default_page_size=25,
    page_param="page",
    page_start=1,
    cursor_param="cursor",
    cursor_start="*",
    sort_param="sort",
    query_param="search",
    select_param="select",
)

_OPENALEX_URL_PREFIX = "https://openalex.org/"
