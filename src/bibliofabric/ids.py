"""Canonical identifier normalization shared by bibliofabric-family clients.

Clients add API-specific encoding on top of these normalizers; the normalizers
themselves never URL-encode.
"""

import re
from collections.abc import Iterable

_DOI_PREFIXES = (
    "https://doi.org/",
    "http://doi.org/",
    "https://dx.doi.org/",
    "http://dx.doi.org/",
    "doi:",
)
_ORCID_PREFIXES = ("https://orcid.org/", "http://orcid.org/", "orcid:")
_ROR_PREFIXES = ("https://ror.org/", "http://ror.org/", "ror:")

_ORCID_LENGTH = 16
_ISSN_LENGTH = 8

_DOI_PATTERN = re.compile(r"^10\.\d{4,9}/\S+$")


def strip_url_prefix(value: str, prefixes: Iterable[str]) -> str:
    """Remove the first matching prefix (case-insensitive) and trim whitespace."""
    stripped = value.strip()
    for prefix in prefixes:
        if stripped.lower().startswith(prefix.lower()):
            return stripped[len(prefix) :].strip()
    return stripped


def normalize_doi(value: str) -> str:
    """Return the bare DOI, lowercased: DOI names are case-insensitive."""
    return strip_url_prefix(value, _DOI_PREFIXES).lower()


def is_doi(value: str) -> bool:
    """Whether the value looks like a bare DOI (``10.<suffix>/<name>``)."""
    return bool(_DOI_PATTERN.match(normalize_doi(value)))


def normalize_orcid(value: str) -> str:
    """Return the ORCID iD in hyphenated form (``0000-0002-1825-0097``)."""
    stripped = strip_url_prefix(value, _ORCID_PREFIXES)
    compact = stripped.replace("-", "").replace(" ", "").upper()
    if len(compact) == _ORCID_LENGTH:
        return "-".join(compact[index : index + 4] for index in range(0, 16, 4))
    return stripped


def normalize_ror(value: str) -> str:
    """Return the bare ROR id, lowercased."""
    return strip_url_prefix(value, _ROR_PREFIXES).lower()


def normalize_issn(value: str) -> str:
    """Return the ISSN in hyphenated uppercase form (``2049-3630``)."""
    stripped = value.strip().upper()
    compact = stripped.replace("-", "").replace(" ", "")
    if (
        len(compact) == _ISSN_LENGTH
        and compact[:4].isdigit()
        and compact[4:-1].isdigit()
        and compact[-1] in "0123456789X"
    ):
        return f"{compact[:4]}-{compact[4:]}"
    return stripped
