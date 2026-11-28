"""Protocol for unwrapping API-specific response envelopes.

A client implements :class:`ResponseUnwrapper` to teach bibliofabric how to
navigate its API's JSON: where the result records live, how to read a single
item, the total count, the next cursor, and the remaining envelope metadata.
:class:`JsonApiUnwrapper` is a ready-made implementation for JSON:API servers.
"""

from typing import Any, Protocol
from urllib.parse import parse_qs, urlsplit


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


class JsonApiUnwrapper:
    """Read a JSON:API envelope (``data``, ``meta``, ``links``).

    Args:
        cursor_param: Name of the cursor query parameter that ``links.next``
            carries on later pages (``"page[cursor]"`` for DataCite).

    Records are the raw JSON:API resource objects (``id``, ``type``,
    ``attributes``, ``relationships``); a client that models flat records
    subclasses this and reshapes them. The total is ``meta.total``, and
    :meth:`meta` returns the rest of the envelope (``meta``, ``links``,
    ``included``).
    """

    def __init__(self, cursor_param: str = "page[cursor]") -> None:
        self._cursor_param = cursor_param

    def _data(self, body: Any) -> Any:
        return body.get("data") if isinstance(body, dict) else None

    def results(self, body: Any) -> list[dict[str, Any]]:
        """Return the ``data`` members that are objects, in order."""
        data = self._data(body)
        if not isinstance(data, list):
            return []
        return [item for item in data if isinstance(item, dict)]

    def item(self, body: Any) -> dict[str, Any]:
        """Return the single ``data`` object, or ``{}`` when it is not one."""
        data = self._data(body)
        return data if isinstance(data, dict) else {}

    def total(self, body: Any) -> int | None:
        """Return ``meta.total`` when it is an integer."""
        meta = body.get("meta") if isinstance(body, dict) else None
        total = meta.get("total") if isinstance(meta, dict) else None
        if isinstance(total, int) and not isinstance(total, bool):
            return total
        return None

    def next_cursor(self, body: Any) -> str | None:
        """Return the cursor query parameter value of ``links.next``, if any."""
        links = body.get("links") if isinstance(body, dict) else None
        next_url = links.get("next") if isinstance(links, dict) else None
        if not isinstance(next_url, str):
            return None
        values = parse_qs(urlsplit(next_url).query).get(self._cursor_param, [])
        return values[0] if values and values[0] else None

    def meta(self, body: Any) -> dict[str, Any]:
        """Return the envelope minus ``data``."""
        if not isinstance(body, dict):
            return {}
        return {key: value for key, value in body.items() if key != "data"}


__all__ = ["JsonApiUnwrapper", "ResponseUnwrapper"]
