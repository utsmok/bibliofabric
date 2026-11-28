"""Canonical identifier normalization shared by bibliofabric-family clients.

Clients add API-specific encoding on top of these normalizers; the normalizers
themselves never URL-encode. Each one strips the resolver URLs and scheme
prefixes its identifier is written with and returns the canonical form. A
value that does not match the known shape comes back stripped and tidied, so
unvetted API fields can pass through without raising.
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
_ROR_PREFIXES = (
    "https://ror.org/",
    "http://ror.org/",
    "https://www.ror.org/",
    "ror.org/",
    "ror:",
)
_ISBN_PREFIXES = (
    "https://www.worldcat.org/isbn/",
    "urn:isbn:",
    "isbn:",
)
_ISNI_PREFIXES = (
    "https://isni.org/isni/",
    "http://isni.org/isni/",
    "https://isni.org/",
    "http://isni.org/",
    "isni:",
)
_ARXIV_PREFIXES = (
    "https://arxiv.org/abs/",
    "http://arxiv.org/abs/",
    "https://export.arxiv.org/abs/",
    "arxiv:",
)
_PMID_PREFIXES = (
    "https://pubmed.ncbi.nlm.nih.gov/",
    "http://pubmed.ncbi.nlm.nih.gov/",
    "https://www.ncbi.nlm.nih.gov/pubmed/",
    "pubmed:",
    "pmid:",
)
_PMCID_PREFIXES = (
    "https://pmc.ncbi.nlm.nih.gov/articles/",
    "http://pmc.ncbi.nlm.nih.gov/articles/",
    "https://www.ncbi.nlm.nih.gov/pmc/articles/",
    "http://www.ncbi.nlm.nih.gov/pmc/articles/",
    "pmcid:",
    "pmc:",
)
_WIKIDATA_PREFIXES = (
    "https://www.wikidata.org/wiki/",
    "http://www.wikidata.org/wiki/",
    "https://www.wikidata.org/entity/",
    "http://www.wikidata.org/entity/",
    "wikidata:",
    "wd:",
)
_GND_PREFIXES = ("https://d-nb.info/gnd/", "http://d-nb.info/gnd/", "gnd:", "gdz:")
_VIAF_PREFIXES = ("https://viaf.org/viaf/", "http://viaf.org/viaf/", "viaf:")

_ORCID_LENGTH = 16
_ISSN_LENGTH = 8
_ISBN_10_LENGTH = 10
_ISNI_LENGTH = 16
_DIGITS_X = "0123456789X"

_DOI_PATTERN = re.compile(r"^10\.\d{4,9}/\S+$")


def _compact(value: str) -> str:
    """Drop hyphens and spaces and uppercase, so an ``x`` check digit becomes ``X``."""
    return value.replace("-", "").replace(" ", "").upper()


def _isbn_13_check_digit(stem: str) -> str:
    """Return the ISBN-13 check digit of a 12-digit stem."""
    total = sum(
        (1 if index % 2 == 0 else 3) * int(digit) for index, digit in enumerate(stem)
    )
    return str((10 - total % 10) % 10)


def _is_valid_isbn_10(isbn10: str) -> bool:
    if (
        len(isbn10) != _ISBN_10_LENGTH
        or not isbn10[:-1].isdigit()
        or isbn10[-1] not in _DIGITS_X
    ):
        return False
    total = sum(
        (10 - index) * (10 if digit == "X" else int(digit))
        for index, digit in enumerate(isbn10)
    )
    return total % 11 == 0


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
    stripped = strip_url_prefix(value, _ORCID_PREFIXES).rstrip("/")
    compact = _compact(stripped)
    if (
        len(compact) == _ORCID_LENGTH
        and compact[:-1].isdigit()
        and compact[-1] in "0123456789X"
    ):
        return "-".join(compact[index : index + 4] for index in range(0, 16, 4))
    return stripped


def normalize_ror(value: str) -> str:
    """Return the bare ROR id, lowercased."""
    return strip_url_prefix(value, _ROR_PREFIXES).rstrip("/").lower()


def normalize_issn(value: str) -> str:
    """Return the ISSN in hyphenated uppercase form (``2049-3630``)."""
    stripped = value.strip().upper()
    compact = _compact(stripped)
    if (
        len(compact) == _ISSN_LENGTH
        and compact[:4].isdigit()
        and compact[4:-1].isdigit()
        and compact[-1] in "0123456789X"
    ):
        return f"{compact[:4]}-{compact[4:]}"
    return stripped


def normalize_isbn(value: str) -> str:
    """Return the ISBN in ISBN-13 form without hyphens (``9780306406157``).

    A valid ISBN-10 converts to its ``978``-prefixed ISBN-13 with a recomputed
    check digit. Any other value comes back compacted: hyphens and spaces
    removed, uppercased.
    """
    compact = _compact(strip_url_prefix(value, _ISBN_PREFIXES))
    if not _is_valid_isbn_10(compact):
        return compact
    stem = f"978{compact[:-1]}"
    return f"{stem}{_isbn_13_check_digit(stem)}"


def normalize_isni(value: str) -> str:
    """Return the ISNI as four groups of four characters (``0000 0001 2109 7254``)."""
    compact = _compact(strip_url_prefix(value, _ISNI_PREFIXES))
    if (
        len(compact) == _ISNI_LENGTH
        and compact[:-1].isdigit()
        and compact[-1] in _DIGITS_X
    ):
        return " ".join(
            compact[index : index + 4] for index in range(0, _ISNI_LENGTH, 4)
        )
    return compact


def normalize_arxiv(value: str) -> str:
    """Return the bare arXiv id (``1706.03762`` or ``hep-th/9901001``).

    Version suffixes are kept as given; old-style ids are lowercased.
    """
    stripped = strip_url_prefix(value, _ARXIV_PREFIXES).rstrip("/")
    category, slash, tail = stripped.partition("/")
    return f"{category.lower()}/{tail.lower()}" if slash else stripped


def normalize_pmid(value: str) -> str:
    """Return the bare PubMed id (``12345678``)."""
    return strip_url_prefix(value, _PMID_PREFIXES).rstrip("/")


def normalize_pmcid(value: str) -> str:
    """Return the PubMed Central id as ``PMC1234567``; bare digits get the prefix."""
    stripped = strip_url_prefix(value, _PMCID_PREFIXES).rstrip("/")
    if stripped.isdigit():
        return f"PMC{stripped}"
    return stripped.upper()


def normalize_wikidata_qid(value: str) -> str:
    """Return the Wikidata entity id as ``Q42`` (or a property id such as ``P3153``)."""
    stripped = strip_url_prefix(value, _WIKIDATA_PREFIXES)
    return stripped.rstrip("/").partition("#")[0].upper()


def normalize_gnd(value: str) -> str:
    """Return the bare GND id (``118540258`` or ``4003233-9``), ``X`` check digits kept."""
    stripped = strip_url_prefix(value, _GND_PREFIXES).rstrip("/")
    return f"{stripped[:-1]}X" if stripped.endswith("x") else stripped


def normalize_viaf(value: str) -> str:
    """Return the bare VIAF cluster number without leading zeros (``54153165``)."""
    stripped = strip_url_prefix(value, _VIAF_PREFIXES).rstrip("/")
    return str(int(stripped)) if stripped.isdigit() else stripped


__all__ = [
    "is_doi",
    "normalize_arxiv",
    "normalize_doi",
    "normalize_gnd",
    "normalize_isbn",
    "normalize_isni",
    "normalize_issn",
    "normalize_orcid",
    "normalize_pmcid",
    "normalize_pmid",
    "normalize_ror",
    "normalize_viaf",
    "normalize_wikidata_qid",
    "strip_url_prefix",
]
