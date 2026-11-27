"""Protocol for unwrapping API-specific response envelopes.

A client implements :class:`ResponseUnwrapper` to teach bibliofabric how to
navigate its API's JSON: where the result records live, how to read a single
item, the total count, the next cursor, and the remaining envelope metadata.
"""

from typing import Any, Protocol


class ResponseUnwrapper(Protocol):
    """Extracts results, totals, cursors, and metadata from an API response."""

    def results(self, body: Any) -> list[dict[str, Any]]:
        """Return the list of raw result records in a search/list response."""
        ...

    def item(self, body: Any) -> dict[str, Any]:
        """Return the raw record for a single-entity response."""
        ...

    def total(self, body: Any) -> int | None:
        """Return the total number of matching records, or ``None`` if unknown."""
        ...

    def next_cursor(self, body: Any) -> str | None:
        """Return the cursor for the next page, or ``None`` on the last page."""
        ...

    def meta(self, body: Any) -> dict[str, Any]:
        """Return the envelope minus the results (facets, group-by, headers)."""
        ...


__all__ = ["ResponseUnwrapper"]
