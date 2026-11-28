"""OpenCitations implementation of bibliofabric's ``ResponseUnwrapper`` protocol.

Both APIs answer every read operation with a top-level JSON list of row
objects; there is no envelope, no total field, and no paging. The resource
clients read the responses directly, so this unwrapper only exists to
satisfy the ``BaseApiClient`` constructor; its readers interpret the list
bodies.
"""

from typing import Any

from bibliofabric.exceptions import NotFoundError


class OpcitatoUnwrapper:
    """Reads results, totals, and metadata from OpenCitations JSON lists."""

    def results(self, body: Any) -> list[dict[str, Any]]:
        """Return the row objects of a top-level list, in order."""
        if not isinstance(body, list):
            return []
        return [row for row in body if isinstance(row, dict)]

    def item(self, body: Any) -> dict[str, Any]:
        """Return the first row of the list.

        Raises :class:`NotFoundError` when the list is empty, which is how
        the APIs answer an unknown identifier.
        """
        rows = self.results(body)
        if not rows:
            raise NotFoundError("OpenCitations answered no row for this identifier.")
        return rows[0]

    def total(self, body: Any) -> int | None:
        """Return the length of the result list (the complete result set)."""
        return len(body) if isinstance(body, list) else None

    def next_cursor(self, body: Any) -> str | None:
        """Return ``None``; no operation of either API pages its results."""
        return None

    def meta(self, body: Any) -> dict[str, Any]:
        """Return ``{}``; a top-level list carries no envelope metadata."""
        return {}


__all__ = ["OpcitatoUnwrapper"]
