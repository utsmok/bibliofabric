"""Crossref-specific response unwrapper.

Teaches bibliofabric how to navigate the Crossref JSON envelope::

    {
        "status": "ok",
        "message-type": "work-list",
        "message-version": "1.0.0",
        "message": {
            "total-results": 186261242,
            "items-per-page": 20,
            "next-cursor": "MTAyNzU1NjE0MzAwMCwxMC4xMDY3...",
            "items": [{...}, {...}],
        },
    }

Single-item routes (``/works/{doi}``, ``/journals/{issn}``, ...) put the
entity itself in ``message``; the remaining envelope metadata (facets,
totals, cursors) surfaces through :meth:`CrossrefUnwrapper.meta`.
"""

from typing import Any

from bibliofabric.unwrap import ResponseUnwrapper


class CrossrefUnwrapper(ResponseUnwrapper):
    """Crossref implementation of the ResponseUnwrapper protocol."""

    @staticmethod
    def _message(body: dict[str, Any]) -> dict[str, Any]:
        """Return the ``message`` body, tolerating list-valued error bodies."""
        message = body.get("message")
        return message if isinstance(message, dict) else {}

    def results(self, body: Any) -> list[dict[str, Any]]:
        """Extract the list of results from ``message.items``."""
        return self._message(body).get("items", [])

    def item(self, body: Any) -> dict[str, Any]:
        """Extract a single item; Crossref GET ``/{route}/{id}`` returns it in ``message``."""
        return self._message(body)

    def total(self, body: Any) -> int | None:
        """Extract the total count from ``message.total-results``."""
        total = self._message(body).get("total-results")
        return int(total) if total is not None else None

    def next_cursor(self, body: Any) -> str | None:
        """Extract the next cursor from ``message.next-cursor``."""
        cursor = self._message(body).get("next-cursor")
        return str(cursor) if cursor is not None else None

    def meta(self, body: Any) -> dict[str, Any]:
        """Return the ``message`` body minus the results (facets, totals)."""
        meta = dict(self._message(body))
        meta.pop("items", None)
        return meta
