"""Zenodo implementation of bibliofabric's ``ResponseUnwrapper`` protocol.

Zenodo search envelopes look like ``{"hits": {"hits": [...], "total": 97},
"links": {...}, "aggregations": {...}}``; single-record routes answer the
record itself. Zenodo pages by page number only, so ``next_cursor`` is
always ``None``.
"""

from typing import Any


class ZenothecaUnwrapper:
    """Extracts results, totals, and metadata from Zenodo JSON."""

    def results(self, body: Any) -> list[dict[str, Any]]:
        """Return the ``hits.hits`` records that are objects, in order."""
        hits = body.get("hits") if isinstance(body, dict) else None
        records = hits.get("hits") if isinstance(hits, dict) else None
        if not isinstance(records, list):
            return []
        return [record for record in records if isinstance(record, dict)]

    def item(self, body: Any) -> dict[str, Any]:
        """Return the record itself; Zenodo single routes are unwrapped."""
        return body if isinstance(body, dict) else {}

    def total(self, body: Any) -> int | None:
        """Return ``hits.total``, or ``None`` when absent."""
        hits = body.get("hits") if isinstance(body, dict) else None
        total = hits.get("total") if isinstance(hits, dict) else None
        if isinstance(total, int) and not isinstance(total, bool):
            return total
        return None

    def next_cursor(self, body: Any) -> str | None:
        """Return ``None``; Zenodo pages by page number only."""
        del body
        return None

    def meta(self, body: Any) -> dict[str, Any]:
        """Return the envelope minus the results (``aggregations``, ``links``, ``page``, ``sortBy``)."""
        if not isinstance(body, dict):
            return {}
        return {key: value for key, value in body.items() if key != "hits"}


__all__ = ["ZenothecaUnwrapper"]
