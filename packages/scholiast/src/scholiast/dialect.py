"""Semantic Scholar query dialect constants.

``SEMANTICSCHOLAR_DIALECT`` tells bibliofabric how the Academic Graph API
names its query parameters. The resource-client base that consumes these
constants lives in :mod:`scholiast._async.resources` (its sync
twin is generated from it).
"""

from bibliofabric.paging import QueryDialect

#: Base URL of the Academic Graph API (papers, authors, patents, snippets).
SEMANTICSCHOLAR_GRAPH_BASE_URL = "https://api.semanticscholar.org/graph/v1"

#: Base URL of the Recommendations API.
SEMANTICSCHOLAR_RECOMMENDATIONS_BASE_URL = (
    "https://api.semanticscholar.org/recommendations/v1"
)

#: Base URL of the Datasets API.
SEMANTICSCHOLAR_DATASETS_BASE_URL = "https://api.semanticscholar.org/datasets/v1"

#: A paper-search page answers at most 100 records (``limit``).
PAPER_SEARCH_MAX_LIMIT = 100

#: One relevance-search offset window cannot pass offset 9900; the API caps
#: ``offset + limit`` at 10,000 for ``/paper/search`` and
#: ``/paper/search/bulk``'s first page.
SEARCH_MAX_OFFSET = 9900

#: ``/paper/batch`` accepts up to 500 ids per request.
PAPER_BATCH_MAX_IDS = 500

#: ``/author/batch`` accepts up to 1000 ids per request.
AUTHOR_BATCH_MAX_IDS = 1000

#: One bulk-search call returns up to 1000 records.
BULK_SEARCH_MAX_LIMIT = 1000

SEMANTICSCHOLAR_DIALECT = QueryDialect(
    page_size_param="limit",
    max_page_size=PAPER_SEARCH_MAX_LIMIT,
    default_page_size=10,
    iterate_page_size=PAPER_SEARCH_MAX_LIMIT,
    count_page_size=1,
    page_param=None,
    offset_param="offset",
    max_offset=SEARCH_MAX_OFFSET,
    sort_param=None,
    query_param="query",
    select_param="fields",
)
