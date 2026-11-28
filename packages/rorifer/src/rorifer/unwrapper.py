"""ROR implementation of bibliofabric's ``ResponseUnwrapper`` protocol.

ROR envelopes look like ``{"items": [...], "number_of_results": 148516,
"meta": {...}}``. A rejected request (an unknown filter key, a page above
500, malformed ``query.advanced`` syntax) comes back as HTTP 200 with an
``{"errors": [...]}`` body, so every reader raises on that shape instead of
reporting an empty result.
"""

from typing import Any

from bibliofabric.exceptions import ConfigurationError


class RoriferUnwrapper:
    """Extracts results, totals, and metadata from ROR JSON."""

    def results(self, body: Any) -> list[dict[str, Any]]:
        """Return the ``items`` records that are objects, in order."""
        self._raise_errors(body)
        items = body.get("items") if isinstance(body, dict) else None
        if not isinstance(items, list):
            return []
        return [item for item in items if isinstance(item, dict)]

    def item(self, body: Any) -> dict[str, Any]:
        """Return the record itself; ROR single routes are unwrapped."""
        self._raise_errors(body)
        return body if isinstance(body, dict) else {}

    def total(self, body: Any) -> int | None:
        """Return ``number_of_results``, or ``None`` when absent."""
        self._raise_errors(body)
        total = body.get("number_of_results") if isinstance(body, dict) else None
        if isinstance(total, int) and not isinstance(total, bool):
            return total
        return None

    def next_cursor(self, body: Any) -> str | None:
        """Return ``None``; ROR pages by page number only."""
        return None

    def meta(self, body: Any) -> dict[str, Any]:
        """Return the facet counts (``types``, ``countries``, ``continents``, ``statuses``) and ``time_taken``."""
        self._raise_errors(body)
        if not isinstance(body, dict):
            return {}
        facets = body.get("meta")
        page_meta: dict[str, Any] = dict(facets) if isinstance(facets, dict) else {}
        if "time_taken" in body:
            page_meta["time_taken"] = body["time_taken"]
        return page_meta

    @staticmethod
    def _raise_errors(body: Any) -> None:
        errors = body.get("errors") if isinstance(body, dict) else None
        if errors:
            messages = "; ".join(str(error) for error in errors)
            raise ConfigurationError(f"ROR rejected the request: {messages}")


__all__ = ["RoriferUnwrapper"]
