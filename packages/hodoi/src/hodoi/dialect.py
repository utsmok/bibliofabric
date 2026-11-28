"""Constants of the DOI System proxy at doi.org."""

import re
from functools import lru_cache

from bibliofabric.exceptions import ConfigurationError

#: The DOI System proxy server.
DOI_BASE_URL = "https://doi.org"

#: Comma-separated DOIs per ``/ra/`` request. A list of 200 short DOIs was
#: accepted on 2026-11-27; a 500-DOI URL answered HTTP 414 (URI Too Long).
#: 100 keeps the URI well below the server limit even for long DOI suffixes.
RA_BATCH_SIZE = 100

_DOI_BODY = re.compile(r"^10\.\d{4,9}/\S+$")

#: Path prefixes and schemes that wrap a bare DOI.
_DOI_URL_PREFIXES = (
    "https://doi.org/",
    "http://doi.org/",
    "https://dx.doi.org/",
    "http://dx.doi.org/",
    "info:doi:",
    "doi:",
)


def strip_doi_form(value: str) -> str:
    """Strip DOI URL and ``doi:`` wrappers without validating the result.

    The ``/ra/`` route answers malformed strings itself (``Invalid DOI``),
    so the lookup sends whatever it gets after removing the wrappers.
    """
    text = value.strip()
    lowered = text.lower()
    for prefix in _DOI_URL_PREFIXES:
        if lowered.startswith(prefix):
            return text[len(prefix) :]
    return text


@lru_cache(maxsize=4096)
def normalize_doi(value: str) -> str:
    """Return the bare DOI for a DOI, DOI URL, or ``doi:`` string.

    Accepts ``10.1038/nature12373``, ``https://doi.org/10.1038/nature12373``,
    ``http://dx.doi.org/10.1038/nature12373``, and ``doi:10.1038/nature12373``.
    Anything else raises :class:`bibliofabric.exceptions.ConfigurationError`.
    """
    text = strip_doi_form(value)
    if not _DOI_BODY.match(text):
        raise ConfigurationError(
            f"Not a DOI name (expected 10.<registrant>/<suffix>): {value!r}."
        )
    return text


__all__ = ["DOI_BASE_URL", "RA_BATCH_SIZE", "normalize_doi", "strip_doi_form"]
