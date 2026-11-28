"""Semantic Scholar query dialect constants.

``SEMANTICSCHOLAR_DIALECT`` tells bibliofabric how the Academic Graph API
names its query parameters. The resource-client base that consumes these
constants lives in :mod:`scholiast._async.resources` (its sync
twin is generated from it).
"""

from dataclasses import replace

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

#: One paper-search window cannot pass offset 9900; the API caps
#: ``offset + limit`` at 10,000 on ``/paper/search``.
SEARCH_MAX_OFFSET = 9900

#: ``/paper/batch`` accepts up to 500 ids per request.
PAPER_BATCH_MAX_IDS = 500

#: ``/author/batch`` accepts up to 1000 ids per request.
AUTHOR_BATCH_MAX_IDS = 1000

#: An author-search page answers at most 1000 records (``limit``).
AUTHOR_SEARCH_MAX_LIMIT = 1000

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

#: The dialect of ``/author/search``: a page holds up to 1000 authors. The
#: offset window is the same as for papers (the API answers 400 with
#: ``offset + limit must be < 10000``).
SEMANTICSCHOLAR_AUTHOR_DIALECT = replace(
    SEMANTICSCHOLAR_DIALECT,
    max_page_size=AUTHOR_SEARCH_MAX_LIMIT,
)
