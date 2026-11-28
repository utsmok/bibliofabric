"""bibliofabric ``ResponseUnwrapper`` for the parsed arXiv feed.

The client parses each Atom feed with :func:`archeion.atom.parse_feed`
first; this unwrapper then reads that dict, so the framework helpers see the
same shape as for a JSON API.
"""

from typing import Any


class ArcheionUnwrapper:
    """Extracts entries, totals, and metadata from a parsed feed."""

    def results(self, body: Any) -> list[dict[str, Any]]:
        """Return the entry dicts in feed order."""
        entries = body.get("entries") if isinstance(body, dict) else None
        if not isinstance(entries, list):
            return []
        return [entry for entry in entries if isinstance(entry, dict)]

    def item(self, body: Any) -> dict[str, Any]:
        """Return the first entry, or an empty dict for an empty feed."""
        results = self.results(body)
        return results[0] if results else {}

    def total(self, body: Any) -> int | None:
        """Return ``opensearch:totalResults``."""
        total = body.get("total") if isinstance(body, dict) else None
        return total if isinstance(total, int) else None

    def next_cursor(self, body: Any) -> str | None:
        """Return ``None``; the API pages by ``start`` offset."""
        del body
        return None

    def meta(self, body: Any) -> dict[str, Any]:
        """Return the feed fields other than the entries."""
        if not isinstance(body, dict):
            return {}
        return {key: value for key, value in body.items() if key != "entries"}


__all__ = ["ArcheionUnwrapper"]
