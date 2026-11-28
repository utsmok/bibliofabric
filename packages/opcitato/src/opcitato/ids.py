"""Identifier parsing and validation for OpenCitations.

OpenCitations packs several identifiers into one space-separated string
(``citing`` and ``cited`` of the Index API, ``id`` of the Meta API) and
requires prefixed identifiers (``doi:...``, ``omid:br/...``) in path
parameters. The helpers here split those strings into typed identifiers
and validate and percent-encode path identifiers before a request is sent.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from urllib.parse import quote

from bibliofabric.exceptions import ConfigurationError

from .dialect import (
    INDEX_ID_SCHEMES,
    META_ID_SCHEMES,
    MULTI_ID_SEPARATOR,
    PERSON_ID_SCHEMES,
)

#: Shape of a single Open Citation Identifier value, ``first-second``.
_OCI_SHAPE = re.compile(r"[0-9]+-[0-9]+")


@dataclass(frozen=True, slots=True)
class ParsedIdentifier:
    """One prefixed identifier of an OpenCitations record.

    ``scheme`` is the lowercase prefix (``doi``, ``omid``, ``pmid``,
    ``openalex``, ``issn``, ``isbn``, ``pmcid``, or ``orcid``) and
    ``value`` the identifier without the prefix (an OMID keeps its
    ``br/`` or ``ra/`` part, as in ``br/06120344846``).
    """

    scheme: str
    value: str

    def __str__(self) -> str:
        return f"{self.scheme}:{self.value}"


def parse_identifiers(text: str) -> list[ParsedIdentifier]:
    """Split a space-separated identifier string into typed identifiers.

    ``"omid:br/06120344846 doi:10.1038/nature12373"`` becomes two
    :class:`ParsedIdentifier` entries. Raises :class:`ConfigurationError`
    when a part carries no ``scheme:`` prefix, because every identifier
    OpenCitations returns is prefixed and a bare part would hide an
    upstream format change.
    """
    identifiers: list[ParsedIdentifier] = []
    for part in text.split():
        scheme, separator, value = part.partition(":")
        if not separator or not scheme or not value:
            raise ConfigurationError(
                f"OpenCitations identifier {part!r} in {text!r} carries no "
                "'scheme:value' prefix."
            )
        identifiers.append(ParsedIdentifier(scheme.lower(), value))
    return identifiers


def _require_prefixed(value: str, *, schemes: frozenset[str], usage: str) -> str:
    """Return ``value`` as a percent-encoded ``scheme:value`` path segment.

    The identifier travels in the URL path, so characters with a syntactic
    meaning are encoded; a DOI that contains ``#`` or ``?`` would otherwise
    cut the path short. Raises :class:`ConfigurationError` for blanks,
    whitespace, a missing prefix, and a scheme the operation rejects.
    """
    identifier = value.strip()
    if not identifier:
        raise ConfigurationError(f"OpenCitations {usage} must be non-empty.")
    if any(character.isspace() for character in identifier):
        raise ConfigurationError(
            f"OpenCitations {usage} must not contain whitespace, got {value!r}."
        )
    scheme, separator, id_value = identifier.partition(":")
    if not separator or not scheme or not id_value:
        raise ConfigurationError(
            f"OpenCitations {usage} must be prefixed as 'scheme:value' "
            f"(for example 'doi:10.1038/nature12373'), got {value!r}."
        )
    if scheme.lower() not in schemes:
        accepted = ", ".join(sorted(schemes))
        raise ConfigurationError(
            f"OpenCitations {usage} uses unsupported scheme {scheme!r}; "
            f"accepted schemes are: {accepted}. The API answers 400 for "
            f"other schemes, including bare ids."
        )
    # The scheme prefix and the identifier keep their separators (``:`` and
    # ``/``) because the routes are written for them, as in
    # ``/citations/doi:10.1038/nature12373`` and ``/author/omid:ra/0601``.
    return quote(f"{scheme.lower()}:{id_value}", safe="/:")


def normalize_index_id(value: str) -> str:
    """Validate one Index API identifier for the URL path.

    Accepts the schemes the Index API documents (``omid``, ``doi``,
    ``pmid``, ``issn``, ``isbn``) and returns the identifier percent-encoded.
    Raises :class:`ConfigurationError` for a bare id or an unsupported
    scheme, which the API would answer with 400.
    """
    return _require_prefixed(value, schemes=INDEX_ID_SCHEMES, usage="index id")


def normalize_meta_ids(value: str | Sequence[str]) -> str:
    """Validate Meta identifiers and join them with the ``__`` separator.

    Accepts one identifier or a list of them (a single string may already
    carry the ``__`` separator). Each identifier must use a scheme the Meta
    ``/metadata`` operation documents, and comes back percent-encoded.
    Raises :class:`ConfigurationError` otherwise.
    """
    parts = value.split(MULTI_ID_SEPARATOR) if isinstance(value, str) else list(value)
    if not parts:
        raise ConfigurationError("OpenCitations meta ids must be non-empty.")
    validated = [
        _require_prefixed(part, schemes=META_ID_SCHEMES, usage="meta id")
        for part in parts
    ]
    return MULTI_ID_SEPARATOR.join(validated)


def normalize_person_id(value: str) -> str:
    """Validate a Meta person identifier (``orcid:...`` or ``omid:ra/...``).

    Raises :class:`ConfigurationError` for any other scheme.
    """
    return _require_prefixed(value, schemes=PERSON_ID_SCHEMES, usage="person id")


def normalize_issn(value: str) -> str:
    """Validate that ``value`` is an ``issn:`` id, as the venue count route needs."""
    return _require_prefixed(value, schemes=frozenset({"issn"}), usage="venue id")


def normalize_oci(value: str) -> str:
    """Normalize an Open Citation Identifier to its ``first-second`` form.

    The ``oci:`` prefix is optional on input and is never sent, because the
    Index ``/citation/{oci}`` operation expects the bare numbers. Raises
    :class:`ConfigurationError` for any other shape.
    """
    identifier = value.strip()
    if identifier.lower().startswith("oci:"):
        identifier = identifier[4:]
    if not _OCI_SHAPE.fullmatch(identifier):
        raise ConfigurationError(
            f"OpenCitations oci must look like '1-8' or 'oci:1-8' "
            f"(two numbers separated by a dash), got {value!r}."
        )
    return identifier


__all__ = [
    "ParsedIdentifier",
    "normalize_index_id",
    "normalize_issn",
    "normalize_meta_ids",
    "normalize_oci",
    "normalize_person_id",
    "parse_identifiers",
]
