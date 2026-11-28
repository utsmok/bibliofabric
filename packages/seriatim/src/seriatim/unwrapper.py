"""Minimal response unwrapper for the ISSN Portal.

The JSON-LD record routes answer a single node with no envelope, and the
HTML routes are read outside the unwrapper. The bibliofabric resource
plumbing still requires an unwrapper; the methods below treat the whole
body as the item and report no totals or metadata.
"""

from typing import Any


class SeriatimUnwrapper:
    """Treats the JSON body as the item; there is no envelope to unwrap."""

    def results(self, body: Any) -> list[dict[str, Any]]:
        """Return ``[]``; the Portal has no list envelope."""
        return []

    def item(self, body: Any) -> dict[str, Any]:
        """Return the body itself when it is a JSON object."""
        return body if isinstance(body, dict) else {}

    def total(self, body: Any) -> int | None:
        """Return ``None``; record routes carry no total."""
        return None

    def next_cursor(self, body: Any) -> str | None:
        """Return ``None``; there is no cursor paging."""
        return None

    def meta(self, body: Any) -> dict[str, Any]:
        """Return an empty metadata mapping."""
        return {}


__all__ = ["SeriatimUnwrapper"]
