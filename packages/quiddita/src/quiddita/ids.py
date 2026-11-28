"""Wikidata identifier helpers."""

import re

from bibliofabric.exceptions import ConfigurationError

_ID_RE = re.compile(r"^([QPLM])?([0-9]+)$", re.IGNORECASE)

_URL_PREFIXES = (
    "https://www.wikidata.org/wiki/",
    "http://www.wikidata.org/wiki/",
    "https://www.wikidata.org/entity/",
    "http://www.wikidata.org/entity/",
    "https://wikidata.org/wiki/",
    "https://wikidata.org/entity/",
)


def normalize_wikidata_id(value: str) -> str:
    """Return the bare canonical Wikidata id (``Q42``, ``P31``, ``L1``).

    Accepts the id itself (any letter case), the wiki URL form
    (``https://www.wikidata.org/wiki/Q42``), and the entity URL form
    (``https://www.wikidata.org/entity/Q42``). Raises
    :class:`~bibliofabric.exceptions.ConfigurationError` for anything else.
    """
    text = value.strip()
    for prefix in _URL_PREFIXES:
        if text.startswith(prefix):
            text = text[len(prefix) :]
            break
    match = _ID_RE.match(text)
    if match is None:
        raise ConfigurationError(
            f"Expected a Wikidata id such as 'Q42', 'P31' or 'L1', got {value!r}."
        )
    kind, number = match.groups()
    prefix = kind if kind is not None else "Q"
    if prefix == "M":
        raise ConfigurationError(
            f"MediaInfo ids ({value!r}) are not supported by this client."
        )
    return f"{prefix.upper()}{number}"


__all__ = ["normalize_wikidata_id"]
