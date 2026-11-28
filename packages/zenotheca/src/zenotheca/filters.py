"""Helpers for the Elasticsearch ``q`` query-string syntax of Zenodo.

The ``q`` parameter of the records and communities routes takes an
Elasticsearch query string. These helpers quote the values correctly and
name the verified search fields. Search fields that Zenodo documents but
that this study did not verify stay usable through :func:`term` and
:func:`phrase`.
"""

from bibliofabric.exceptions import ConfigurationError

#: Characters that cannot appear unquoted inside an Elasticsearch term.
_TERMINAL = frozenset(' \t\r\n"\\^`{}[]()<>!|~*?:&+=,;/')


def _quote_term(value: str, *, field: str) -> str:
    text = value.strip()
    if not text:
        raise ConfigurationError(f"The {field} search value must be non-empty.")
    if any(char in text for char in '"\\'):
        raise ConfigurationError(
            f"The {field} search value cannot contain '\"' or '\\', got {value!r}."
        )
    return text


def term(field: str, value: str) -> str:
    """Return ``field:value`` as a bare term clause.

    Use this for values without whitespace or special characters, such as
    ``term("communities", "ror-data")``. Anything else needs
    :func:`phrase`.
    """
    text = _quote_term(value, field=field)
    if any(char in text for char in _TERMINAL):
        raise ConfigurationError(
            f"The value for {field!r} contains a reserved character; use "
            f"phrase({field!r}, ...) instead."
        )
    return f"{field}:{text}"


def phrase(field: str, value: str) -> str:
    """Return ``field:"value"`` as a quoted phrase clause (``title:"ROR Data"``)."""
    text = _quote_term(value, field=field)
    return f'{field}:"{text}"'


def community(slug: str) -> str:
    """Return the ``communities:<slug>`` clause (verified 2026-11-27)."""
    return term("communities", slug)


def resource_type(value: str) -> str:
    """Return the ``type:<value>`` clause (``dataset``, ``publication``, ...)."""
    return term("type", value)


def any_of(*clauses: str) -> str:
    """Join clauses with ``OR``; a single clause passes through unchanged."""
    if not clauses:
        raise ConfigurationError("any_of needs at least one clause.")
    if len(clauses) == 1:
        return clauses[0]
    return f"({' OR '.join(clauses)})"


def all_of(*clauses: str) -> str:
    """Join clauses with the implicit ``AND`` of the query string."""
    if not clauses:
        raise ConfigurationError("all_of needs at least one clause.")
    return " ".join(clauses)


__all__ = [
    "all_of",
    "any_of",
    "community",
    "phrase",
    "resource_type",
    "term",
]
