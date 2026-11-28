"""Europe PMC implementation of bibliofabric's ``ResponseUnwrapper`` protocol.

Every Europe PMC list envelope nests its records under a wrapper key:
``resultList.result`` for search, ``referenceList.reference`` for references,
``citationList.citation`` for citations, and ``databaseLinkList.databaseLink``
for database links. The total is always ``hitCount`` and the search cursor is
``nextCursorMark`` (which repeats unchanged when the result set is exhausted).
"""

from typing import Any

_LIST_KEYS: tuple[tuple[str, str], ...] = (
    ("resultList", "result"),
    ("referenceList", "reference"),
    ("citationList", "citation"),
    ("databaseLinkList", "databaseLink"),
)


class EuropaeaUnwrapper:
    """Extracts results, totals, cursors, and metadata from Europe PMC JSON."""

    def results(self, body: Any) -> list[dict[str, Any]]:
        """Return the records of the list wrapper the body carries, in order."""
        if not isinstance(body, dict):
            return []
        for outer, inner in _LIST_KEYS:
            wrapper = body.get(outer)
            if isinstance(wrapper, dict):
                records = wrapper.get(inner)
                if isinstance(records, list):
                    return [record for record in records if isinstance(record, dict)]
        return []

    def item(self, body: Any) -> dict[str, Any]:
        """Return the record of a single-entity route.

        ``/article/{source}/{id}`` wraps its record in a ``result`` key
        (alongside ``hitCount`` and the request echo); other single routes
        answer the record itself.
        """
        if not isinstance(body, dict):
            return {}
        record = body.get("result")
        if isinstance(record, dict):
            return record
        return body

    def total(self, body: Any) -> int | None:
        """Return ``hitCount``, or ``None`` when absent."""
        total = body.get("hitCount") if isinstance(body, dict) else None
        if isinstance(total, int) and not isinstance(total, bool):
            return total
        return None

    def next_cursor(self, body: Any) -> str | None:
        """Return ``nextCursorMark`` when it points to a further page.

        The API repeats the same cursor once the list is exhausted; the
        framework treats that as the end of iteration.
        """
        cursor = body.get("nextCursorMark") if isinstance(body, dict) else None
        return cursor if isinstance(cursor, str) else None

    def meta(self, body: Any) -> dict[str, Any]:
        """Return the envelope minus the list wrapper and its total."""
        if not isinstance(body, dict):
            return {}
        excluded = {"resultList", "referenceList", "citationList", "hitCount"}
        return {key: value for key, value in body.items() if key not in excluded}


__all__ = ["EuropaeaUnwrapper"]
