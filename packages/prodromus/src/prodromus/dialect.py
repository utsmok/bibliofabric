"""Constants and path helpers of the bioRxiv API (``api.biorxiv.org``)."""

import re
from datetime import date

from bibliofabric.exceptions import ConfigurationError

#: Base URL of the API; it serves bioRxiv and medRxiv.
BIORXIV_API_BASE_URL = "https://api.biorxiv.org"

#: The two preprint servers the API serves.
SERVERS = frozenset({"biorxiv", "medrxiv"})

#: Records per page of the ``details`` routes.
DETAILS_PAGE_SIZE = 30

#: Records per page of the ``pubs``, ``pub``, ``publisher``, and ``funder``
#: routes.
PUBLISHED_PAGE_SIZE = 100

#: Statistics intervals: monthly or yearly.
STATISTICS_INTERVALS = frozenset({"m", "y"})

_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def server_segment(server: str) -> str:
    """Return the lower-case server name or raise for an unknown one."""
    wanted = server.strip().lower()
    if wanted not in SERVERS:
        raise ConfigurationError(f"server must be one of {sorted(SERVERS)}.")
    return wanted


def date_range(start: date | str, end: date | str) -> str:
    """Return the ``YYYY-MM-DD/YYYY-MM-DD`` interval segment."""
    first, last = str(start), str(end)
    if not _DATE.match(first) or not _DATE.match(last):
        raise ConfigurationError("start and end must be dates in YYYY-MM-DD form.")
    if first > last:
        raise ConfigurationError(f"start {first} lies after end {last}.")
    return f"{first}/{last}"


__all__ = [
    "BIORXIV_API_BASE_URL",
    "DETAILS_PAGE_SIZE",
    "PUBLISHED_PAGE_SIZE",
    "SERVERS",
    "STATISTICS_INTERVALS",
    "date_range",
    "server_segment",
]
