"""Unwrappers that teach bibliofabric how to read OpenAIRE response envelopes."""

from typing import Any


class OpenAireUnwrapper:
    """Reads the Graph API envelope ``{"header": ..., "results": [...]}``.

    Also covers the ``/research-products/links`` variant, whose header carries
    ``totalLinks``/``totalPages`` instead of ``numFound`` and has no cursor.
    """

    @staticmethod
    def _header(body: Any) -> dict[str, Any]:
        if isinstance(body, dict) and isinstance(body.get("header"), dict):
            return body["header"]
        return {}

    def results(self, body: Any) -> list[dict[str, Any]]:
        """Return the list of raw result records in a search/list response."""
        if isinstance(body, dict) and isinstance(body.get("results"), list):
            return body["results"]
        return []

    def item(self, body: Any) -> dict[str, Any]:
        """Return the raw record for a single-entity response.

        The V3 by-id routes return the record itself, unwrapped.
        """
        if isinstance(body, dict) and isinstance(body.get("results"), list):
            records = body["results"]
            if records and isinstance(records[0], dict):
                return records[0]
        if isinstance(body, dict):
            return body
        raise ValueError("Response body is not a JSON object.")

    def total(self, body: Any) -> int | None:
        """Return the total number of matching records, or ``None`` if unknown."""
        header = self._header(body)
        total = header.get("numFound", header.get("totalLinks"))
        return int(total) if total is not None else None

    def next_cursor(self, body: Any) -> str | None:
        """Return the cursor for the next page, or ``None`` on the last page."""
        cursor = self._header(body).get("nextCursor")
        return str(cursor) if cursor else None

    def meta(self, body: Any) -> dict[str, Any]:
        """Return the envelope minus the results (header, facets, group-by)."""
        if isinstance(body, dict):
            return {key: value for key, value in body.items() if key != "results"}
        return {}


class ScholixUnwrapper:
    """Reads the Scholexplorer envelope ``{"currentPage", "totalLinks",
    "totalPages", "result": [...]}`` — note ``result``, not ``results``."""

    def results(self, body: Any) -> list[dict[str, Any]]:
        """Return the list of raw link records in a search response."""
        if isinstance(body, dict) and isinstance(body.get("result"), list):
            return body["result"]
        return []

    def item(self, body: Any) -> dict[str, Any]:
        """Return the raw record for a single-entity response."""
        if isinstance(body, dict) and isinstance(body.get("result"), list):
            records = body["result"]
            if records and isinstance(records[0], dict):
                return records[0]
        if isinstance(body, dict):
            return body
        raise ValueError("Response body is not a JSON object.")

    def total(self, body: Any) -> int | None:
        """Return the total number of matching links, or ``None`` if unknown."""
        total = body.get("totalLinks") if isinstance(body, dict) else None
        return int(total) if total is not None else None

    def next_cursor(self, body: Any) -> str | None:
        """Scholexplorer has no cursor paging; always ``None``."""
        return None

    def meta(self, body: Any) -> dict[str, Any]:
        """Return the envelope minus the result list."""
        if isinstance(body, dict):
            return {key: value for key, value in body.items() if key != "result"}
        return {}
