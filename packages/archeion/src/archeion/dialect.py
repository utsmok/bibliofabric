"""Constants of the arXiv query API (``export.arxiv.org/api/query``)."""

#: Base URL of the arXiv API. ``/query`` below it is the only read route.
ARXIV_API_BASE_URL = "https://export.arxiv.org/api"

#: Results per request that the API documentation allows. The live API
#: answered 3000 on 2026-11-28, but the documented slice size is 2000.
MAX_RESULTS_PER_PAGE = 2000

#: Results one query reaches through ``start`` and ``max_results`` together,
#: per the API documentation.
MAX_TOTAL_RESULTS = 30_000

#: Default page size of :meth:`QueryClient.search`, as on the API.
DEFAULT_PAGE_SIZE = 10

#: Values of the ``sortBy`` parameter.
SORT_BY = frozenset({"relevance", "lastUpdatedDate", "submittedDate"})

#: Values of the ``sortOrder`` parameter.
SORT_ORDER = frozenset({"ascending", "descending"})

__all__ = [
    "ARXIV_API_BASE_URL",
    "DEFAULT_PAGE_SIZE",
    "MAX_RESULTS_PER_PAGE",
    "MAX_TOTAL_RESULTS",
    "SORT_BY",
    "SORT_ORDER",
]
