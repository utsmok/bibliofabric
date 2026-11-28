"""ROR query dialect constants.

``ROR_DIALECT`` tells bibliofabric how ROR names its query parameters. The
resource-client base that consumes these constants lives in
:mod:`rorifer._async.dialect` (its sync twin is generated from it).
"""

from bibliofabric.paging import QueryDialect

#: Base URL of the ROR v2 API.
ROR_API_BASE_URL = "https://api.ror.org/v2"

#: Path of the ROR API health check, which lives outside the ``/v2`` prefix.
ROR_HEARTBEAT_PATH = "/heartbeat"

#: Base URL of the Zenodo API that hosts the ROR data dumps.
ROR_ZENODO_API_BASE_URL = "https://zenodo.org/api"

#: Host of the Zenodo API; its requests get their own rate class.
ROR_ZENODO_HOST = "zenodo.org"

#: Zenodo community that holds the ROR data dump versions.
ROR_ZENODO_COMMUNITY = "ror-data"

#: Zenodo concept record of the dumps (DOI ``10.5281/zenodo.6347574``). It
#: redirects to the latest release.
ROR_ZENODO_CONCEPT_RECORD_ID = 6347574

#: Records per page of the anonymous Zenodo search. A larger ``size`` is a
#: 400 answer (verified 2026-11-28).
ZENODO_SEARCH_PAGE_SIZE = 25

#: Requests per second that the anonymous Zenodo search accepts. The 31st
#: request in a minute answers 429 ``30 per 1 minute`` (verified 2026-11-28).
ZENODO_SEARCH_REQUESTS_PER_SECOND = 0.5

#: ROR returns exactly this many records per page; there is no page-size
#: parameter.
ROR_PAGE_SIZE = 20

#: ROR answers ``page`` values from 1 to this number, so the API can reach at
#: most ``ROR_MAX_PAGE * ROR_PAGE_SIZE`` records per query.
ROR_MAX_PAGE = 500

#: Organization types accepted by the ``types`` filter and returned in
#: ``Organization.types`` (facets of an unfiltered listing, 2026-11-27).
ORGANIZATION_TYPES = frozenset(
    {
        "archive",
        "company",
        "education",
        "facility",
        "government",
        "healthcare",
        "nonprofit",
        "other",
        "funder",
    }
)

#: Record statuses accepted by the ``status`` filter.
RECORD_STATUSES = frozenset({"active", "inactive", "withdrawn"})

#: Filter keys accepted by the ``filter`` parameter (verified 2026-11-27).
ROR_FILTER_KEYS = frozenset(
    {
        "status",
        "types",
        "country.country_code",
        "country.country_name",
        "locations.geonames_details.country_code",
        "locations.geonames_details.country_name",
        "locations.geonames_details.continent_code",
        "locations.geonames_details.continent_name",
    }
)

ROR_DIALECT = QueryDialect(
    page_size_param=None,
    max_page_size=ROR_PAGE_SIZE,
    default_page_size=ROR_PAGE_SIZE,
    iterate_page_size=ROR_PAGE_SIZE,
    count_page_size=ROR_PAGE_SIZE,
    page_param="page",
    page_start=1,
    max_offset=(ROR_MAX_PAGE - 1) * ROR_PAGE_SIZE,
    sort_param=None,
    query_param="query",
    select_param=None,
)
