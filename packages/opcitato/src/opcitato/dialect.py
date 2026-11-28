"""OpenCitations dialect constants.

Both REST APIs are served by one host and are built with RAMOSE, so they
share the row-shaping parameters (``require``, ``filter``, ``sort``,
``format``, ``json``) and the documented rate limit. The resource clients
that consume these constants live in :mod:`opcitato._async`
(their sync twins are generated from them).
"""

#: Base URL of both OpenCitations APIs (Index and Meta).
OPENCITATIONS_API_BASE_URL = "https://api.opencitations.net"

#: Path prefix of the Index API v2 routes.
INDEX_API_PATH = "index/v2"

#: Path prefix of the Meta API v1 routes.
META_API_PATH = "meta/v1"

#: Number of rows one Index or Meta request returns. There is no paging:
#: every operation answers with the complete result of the query.
UNPAGED = True

#: Separator OpenCitations uses to pack several identifiers into one path
#: segment (documented for the Meta ``/metadata/{ids}`` operation).
MULTI_ID_SEPARATOR = "__"

#: Result representations accepted by the ``format`` parameter. It overrides
#: whatever the ``Accept`` header asks for.
FORMATS = frozenset({"json", "csv"})

#: Identifier schemes the Index API accepts in its ``{id}`` path parameters
#: (documented shape ``(omid|doi|pmid|issn|isbn):(.+)``). The API answers
#: 400 for anything else, including bare DOIs and ``openalex:`` ids.
INDEX_ID_SCHEMES = frozenset({"omid", "doi", "pmid", "issn", "isbn"})

#: Identifier schemes the Meta ``/metadata`` operation accepts (the
#: documented shape also allows ``openalex``, ``pmid``, and ``pmcid``).
META_ID_SCHEMES = frozenset(
    {"doi", "issn", "isbn", "omid", "openalex", "pmid", "pmcid"}
)

#: Identifier schemes the Meta ``/author`` and ``/editor`` operations accept:
#: an ORCID or the OpenCitations id of a responsible entity (``omid:ra/...``).
PERSON_ID_SCHEMES = frozenset({"orcid", "omid"})

__all__ = [
    "FORMATS",
    "INDEX_API_PATH",
    "INDEX_ID_SCHEMES",
    "META_API_PATH",
    "META_ID_SCHEMES",
    "MULTI_ID_SEPARATOR",
    "OPENCITATIONS_API_BASE_URL",
    "PERSON_ID_SCHEMES",
    "UNPAGED",
]
