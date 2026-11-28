"""Constants and identifier helpers of the DOI System proxy at doi.org."""

import re
from collections.abc import Sequence
from functools import lru_cache
from urllib.parse import quote, unquote

from bibliofabric.exceptions import ConfigurationError

#: The DOI System proxy server.
DOI_BASE_URL = "https://doi.org"
#: Comma-separated DOIs per ``/ra/`` request. A list of 200 short DOIs was
#: accepted on 2026-11-27; a 500-DOI URL answered HTTP 414 (URI Too Long).
RA_BATCH_SIZE = 100

#: Longest ``/ra/`` path (in characters, DOIs percent-encoded) the client
#: sends. The limit of the proxy is not documented, so a chunk also ends
#: early when adding its next DOI would pass this size.
RA_MAX_PATH_CHARS = 4000

#: A bare DOI name: the ``10.`` prefix with a four to nine digit registrant,
#: a slash, and a suffix that neither starts nor ends with whitespace.
_DOI_BODY = re.compile(r"10\.\d{4,9}/\S(?:.*\S)?")

#: Path prefixes and schemes that wrap a bare DOI.
_DOI_URL_PREFIXES = (
    "https://doi.org/",
    "http://doi.org/",
    "https://dx.doi.org/",
    "http://dx.doi.org/",
)

#: Wrappers that carry the bare DOI literally.
_DOI_NAME_PREFIXES = ("info:doi:", "doi:")

#: Characters of a DOI that travel unescaped in the URL path. The DOI
#: Resolution Documentation lists the characters to encode: ``%``, ``"``,
#: ``#``, space, and ``?`` must be encoded; ``<``, ``>``, ``{``, ``}``, ``^``,
#: ``[``, ``]``, backtick, ``|``, ``\``, and ``+`` should be; non-ASCII
#: characters travel as percent-encoded UTF-8. The comma is encoded because
#: it separates the DOIs of the ``/ra/`` route (the proxy decodes each DOI
#: after splitting, verified 2026-11-28).
_DOI_PATH_SAFE = "/:;@&=!$'()*-._~"


def strip_doi_form(value: str) -> str:
    """Strip DOI URL and ``doi:`` wrappers without validating the result.

    A URL wrapper carries the DOI percent-encoded, as in
    ``https://doi.org/10.1000/res%23test``; the function decodes it. In a
    URL a raw ``?`` starts the query string and a raw ``#`` the fragment,
    so both are cut, as in ``https://doi.org/10.1038/nature12373?from=x``.
    A bare DOI keeps them, because both are legal characters of a DOI
    name. The ``/ra/`` route answers malformed strings itself (``Invalid
    DOI``), so the lookup sends whatever it gets after the wrapper is
    removed.
    """
    text = value.strip()
    lowered = text.lower()
    for prefix in _DOI_URL_PREFIXES:
        if lowered.startswith(prefix):
            rest = text[len(prefix) :]
            return unquote(rest.partition("#")[0].partition("?")[0])
    for prefix in _DOI_NAME_PREFIXES:
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
    if not _DOI_BODY.fullmatch(text):
        raise ConfigurationError(
            f"Not a DOI name (expected 10.<registrant>/<suffix>): {value!r}."
        )
    return text


def doi_path(doi: str) -> str:
    """Return ``doi`` percent-encoded for the path of a doi.org URL.

    The DOI ``10.1000/res#test`` becomes ``10.1000/res%23test``, the form
    the proxy resolves (see the DOI Resolution Documentation, section 2).
    """
    return quote(doi, safe=_DOI_PATH_SAFE)


def ra_chunks(dois: Sequence[str]) -> list[str]:
    """Group percent-encoded DOIs into the comma-separated bodies of ``/ra/`` paths.

    A chunk holds at most :data:`RA_BATCH_SIZE` DOIs and stays under
    :data:`RA_MAX_PATH_CHARS` characters, so long DOIs form more, smaller
    requests. A single DOI that is longer than the budget travels alone.
    """
    chunks: list[str] = []
    current: list[str] = []
    length = 0
    for doi in dois:
        size = len(doi) + 1
        if current and (
            len(current) >= RA_BATCH_SIZE or length + size > RA_MAX_PATH_CHARS
        ):
            chunks.append(",".join(current))
            current, length = [], 0
        current.append(doi)
        length += size
    if current:
        chunks.append(",".join(current))
    return chunks


__all__ = [
    "DOI_BASE_URL",
    "RA_BATCH_SIZE",
    "RA_MAX_PATH_CHARS",
    "doi_path",
    "normalize_doi",
    "ra_chunks",
    "strip_doi_form",
]
