"""DOAJ implementation of bibliofabric's ``ResponseUnwrapper`` protocol.

DOAJ search envelopes look like ``{"total": 23831, "page": 1,
"pageSize": 10, "timestamp": "...", "query": "...", "results": [...],
"next": "...", "prev": "...", "last": "..."}``. Pages after the first carry
``next`` and ``prev`` as full URLs, so paging runs on the ``page`` number
and the unwrapper reports no cursor.
"""

from typing import Any


class DiurnaliaUnwrapper:
    """Extracts results, totals, and metadata from DOAJ JSON."""

    def results(self, body: Any) -> list[dict[str, Any]]:
        """Return the ``results`` records that are objects, in order."""
        results = body.get("results") if isinstance(body, dict) else None
        if not isinstance(results, list):
            return []
        return [item for item in results if isinstance(item, dict)]

    def item(self, body: Any) -> dict[str, Any]:
        """Return the record itself; DOAJ single records are unwrapped."""
        return body if isinstance(body, dict) else {}

    def total(self, body: Any) -> int | None:
        """Return ``total``, or ``None`` when absent."""
        total = body.get("total") if isinstance(body, dict) else None
        if isinstance(total, int) and not isinstance(total, bool):
            return total
        return None

    def next_cursor(self, body: Any) -> str | None:
        """Return ``None``; DOAJ pages by page number only."""
        del body
        return None

    def meta(self, body: Any) -> dict[str, Any]:
        """Return the envelope minus the results.

        Carries ``total``, ``page``, ``pageSize``, ``timestamp``, ``query``
        and the ``next``, ``prev``, ``last`` page URLs when present.
        """
        if not isinstance(body, dict):
            return {}
        return {key: value for key, value in body.items() if key != "results"}


__all__ = ["DiurnaliaUnwrapper"]
