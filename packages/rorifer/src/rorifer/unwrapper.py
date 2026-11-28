"""ROR implementation of bibliofabric's ``ResponseUnwrapper`` protocol.

ROR envelopes look like ``{"items": [...], "number_of_results": 148516,
"meta": {...}}``. A rejected request (an unknown filter key, a page above
500, malformed ``query.advanced`` syntax) comes back as HTTP 200 with an
``{"errors": [...]}`` body, so every reader raises on that shape instead of
reporting an empty result. A body of another shape raises as well.
"""

from typing import Any

from bibliofabric.exceptions import APIError, ConfigurationError


class RoriferUnwrapper:
    """Extracts results, totals, and metadata from ROR JSON."""

    def results(self, body: Any) -> list[dict[str, Any]]:
        """Return the ``items`` of a search envelope.

        Raises:
            ConfigurationError: The body carries ROR's ``errors``.
            APIError: The body has no ``items`` list.
        """
        items = self._object(body).get("items")
        if not isinstance(items, list):
            raise APIError("ROR answer has no items list", body=body)
        return items

    def item(self, body: Any) -> dict[str, Any]:
        """Return the record itself; ROR single routes are unwrapped.

        Raises:
            ConfigurationError: The body carries ROR's ``errors``.
            APIError: The body is not a JSON object.
        """
        return self._object(body)

    def total(self, body: Any) -> int | None:
        """Return ``number_of_results``, or ``None`` when absent."""
        total = self._object(body).get("number_of_results")
        if isinstance(total, int) and not isinstance(total, bool):
            return total
        return None

    def next_cursor(self, body: Any) -> str | None:
        """Return ``None``; ROR pages by page number only."""
        del body
        return None

    def meta(self, body: Any) -> dict[str, Any]:
        """Return the facet counts (``types``, ``countries``, ``continents``, ``statuses``) and ``time_taken``."""
        envelope = self._object(body)
        facets = envelope.get("meta")
        page_meta: dict[str, Any] = dict(facets) if isinstance(facets, dict) else {}
        if "time_taken" in envelope:
            page_meta["time_taken"] = envelope["time_taken"]
        return page_meta

    @staticmethod
    def _object(body: Any) -> dict[str, Any]:
        """Return ``body`` as the JSON object of a ROR answer.

        Raises:
            ConfigurationError: The body carries ROR's ``errors``.
            APIError: The body is not a JSON object.
        """
        if not isinstance(body, dict):
            raise APIError(
                f"ROR answer is not a JSON object but {type(body).__name__}",
                body=body,
            )
        errors = body.get("errors")
        if errors:
            messages = "; ".join(str(error) for error in errors)
            raise ConfigurationError(f"ROR rejected the request: {messages}")
        return body


__all__ = ["RoriferUnwrapper"]
