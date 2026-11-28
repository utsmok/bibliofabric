"""Unwrapper for the DOI System proxy answers.

The DOI client reads responses directly instead of through the resource
layer, so this unwrapper only exists to satisfy the ``BaseApiClient``
constructor. Its readers interpret the plain JSON bodies of doi.org.
"""

from typing import Any

from bibliofabric.exceptions import ConfigurationError


class HodoiUnwrapper:
    """Extracts records from the flat JSON bodies of doi.org."""

    def results(self, body: Any) -> list[dict[str, Any]]:
        """Return the entries of a JSON list body."""
        self._raise_errors(body)
        if isinstance(body, list):
            return [entry for entry in body if isinstance(entry, dict)]
        return []

    def item(self, body: Any) -> dict[str, Any]:
        """Return the body itself; doi.org single routes are unwrapped."""
        self._raise_errors(body)
        return body if isinstance(body, dict) else {}

    def total(self, body: Any) -> int | None:
        """Return ``None``; doi.org publishes no totals."""
        return None

    def next_cursor(self, body: Any) -> str | None:
        """Return ``None``; doi.org has no paging."""
        return None

    def meta(self, body: Any) -> dict[str, Any]:
        """Return an empty mapping; doi.org publishes no page metadata."""
        return {}

    @staticmethod
    def _raise_errors(body: Any) -> None:
        errors = body.get("errors") if isinstance(body, dict) else None
        if errors:
            messages = "; ".join(str(error) for error in errors)
            raise ConfigurationError(f"doi.org rejected the request: {messages}")


__all__ = ["HodoiUnwrapper"]
