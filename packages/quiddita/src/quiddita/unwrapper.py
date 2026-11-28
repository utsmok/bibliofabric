"""Wikidata implementation of bibliofabric's ``ResponseUnwrapper`` protocol.

MediaWiki Action API errors come back as HTTP 200 with an ``error`` body.

Soft errors (an unknown parameter value, an unknown module, too many ids)
and hard errors alike answer with 200, so the unwrapper raises on that shape
instead of reporting an empty result. ``no-such-entity`` maps to
:class:`~bibliofabric.exceptions.NotFoundError`; everything else raises
:class:`ConfigurationError`. The unwrapper also reads ``search`` records,
``searchinfo`` metadata, and single entities out of the envelopes.
"""

from typing import Any

from bibliofabric.exceptions import ConfigurationError, NotFoundError


class QuidditaUnwrapper:
    """Extracts results, totals, and metadata from Action API JSON."""

    def _raise_errors(self, body: Any) -> None:
        error = body.get("error") if isinstance(body, dict) else None
        if error:
            code = error.get("code", "unknown") if isinstance(error, dict) else error
            info = error.get("info", "") if isinstance(error, dict) else ""
            message = f"Wikidata API rejected the request: {code}: {info}"
            if code == "no-such-entity":
                raise NotFoundError(message)
            raise ConfigurationError(message)

    def results(self, body: Any) -> list[dict[str, Any]]:
        """Return the ``search`` records of a ``wbsearchentities`` response."""
        self._raise_errors(body)
        results = body.get("search") if isinstance(body, dict) else None
        if not isinstance(results, list):
            return []
        return [item for item in results if isinstance(item, dict)]

    def item(self, body: Any) -> dict[str, Any]:
        """Return the single entity of a one-id ``wbgetentities`` response.

        An unknown lexeme or property id answers with a ``missing`` stub
        instead of an error, which raises ``NotFoundError`` here.
        """
        self._raise_errors(body)
        entities = body.get("entities") if isinstance(body, dict) else None
        if isinstance(entities, dict) and len(entities) == 1:
            record = next(iter(entities.values()))
            if isinstance(record, dict):
                if is_missing(record):
                    raise not_found_error(str(record.get("id", "")))
                return record
        return {}

    def total(self, body: Any) -> int | None:
        """Return ``None``; ``wbsearchentities`` reports no total."""
        self._raise_errors(body)
        return None

    def next_cursor(self, body: Any) -> str | None:
        """Return ``None``; search pages by ``continue`` offset, not cursor."""
        self._raise_errors(body)
        return None

    def meta(self, body: Any) -> dict[str, Any]:
        """Return the envelope minus ``search`` (``searchinfo``, ``success``)."""
        self._raise_errors(body)
        if not isinstance(body, dict):
            return {}
        return {key: value for key, value in body.items() if key != "search"}


def is_missing(record: dict[str, Any]) -> bool:
    """Return whether a ``wbgetentities`` record is a ``missing`` stub."""
    return "missing" in record


def rejected_id(body: Any) -> str | None:
    """Return the id that a ``no-such-entity`` error names, if any.

    An unknown item, form, or sense id fails the whole request, and the
    error body carries that id as ``id``.
    """
    error = body.get("error") if isinstance(body, dict) else None
    if isinstance(error, dict) and error.get("code") == "no-such-entity":
        entity_id = error.get("id")
        if isinstance(entity_id, str):
            return entity_id
    return None


def not_found_error(entity_id: str) -> NotFoundError:
    """Build the ``NotFoundError`` for an entity that the API does not know."""
    return NotFoundError(
        "Wikidata API rejected the request: no-such-entity: "
        f'Could not find an entity with the ID "{entity_id}".'
    )


__all__ = ["QuidditaUnwrapper", "is_missing", "not_found_error", "rejected_id"]
