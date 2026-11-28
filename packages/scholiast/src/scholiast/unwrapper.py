"""Semantic Scholar implementation of bibliofabric's ``ResponseUnwrapper``.

Academic Graph envelopes put result lists under ``data`` (searches,
citations, references, author papers) or ``matches`` (autocomplete), and
pagination under ``next`` (next offset) or ``token`` (bulk-search
continuation). Single-entity routes (one paper, one author, one patent,
a recommendations list) answer the record itself or a named list, so
``results`` falls back to those shapes.
"""

from typing import Any


class ScholiastUnwrapper:
    """Extracts results, totals, and metadata from Semantic Scholar JSON."""

    def results(self, body: Any) -> list[dict[str, Any]]:
        """Return the ``data`` records (or ``matches``), in order.

        A body without either key (a single record, a plain release-id
        list) yields no results; those routes read the body directly.
        """
        if not isinstance(body, dict):
            return []
        for key in ("data", "matches", "recommendedPapers"):
            items = body.get(key)
            if isinstance(items, list):
                return [item for item in items if isinstance(item, dict)]
        return []

    def item(self, body: Any) -> dict[str, Any]:
        """Return the record itself; single-entity routes are unwrapped."""
        return body if isinstance(body, dict) else {}

    def total(self, body: Any) -> int | None:
        """Return ``total`` of a search envelope, or ``None`` when absent."""
        total = body.get("total") if isinstance(body, dict) else None
        if isinstance(total, int) and not isinstance(total, bool):
            return total
        return None

    def next_cursor(self, body: Any) -> str | None:
        """Return the continuation for a follow-up request.

        Offset-paged envelopes carry ``next`` (the next offset value);
        bulk search carries ``token``. Both are returned as strings. On
        the last page neither key exists.
        """
        if not isinstance(body, dict):
            return None
        token = body.get("token")
        if isinstance(token, str) and token:
            return token
        for key in ("next", "token"):
            value = body.get(key)
            if isinstance(value, int) and not isinstance(value, bool):
                return str(value)
        return None

    def meta(self, body: Any) -> dict[str, Any]:
        """Return the envelope minus the result list.

        Keeps ``offset``, ``next``, ``token``, ``total``, ``retrievalVersion``
        and any other envelope extras the API adds.
        """
        if not isinstance(body, dict):
            return {}
        skip = {"data", "matches", "recommendedPapers"}
        return {key: value for key, value in body.items() if key not in skip}


__all__ = ["ScholiastUnwrapper"]
