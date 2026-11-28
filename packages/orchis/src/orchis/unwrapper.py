"""ORCID implementation of bibliofabric's ``ResponseUnwrapper`` protocol.

The ORCID search routes answer two envelope shapes over the same Solr index:
``/expanded-search`` returns ``{"expanded-result": [...], "num-found": N}``
and the Solr-compatible ``/search`` returns ``{"result": [...],
"num-found": N}``. Record and section routes answer the object itself, so
``item()`` returns the body unchanged.
"""

from typing import Any


class OrchisUnwrapper:
    """Extracts results, totals, and metadata from ORCID JSON."""

    def results(self, body: Any) -> list[dict[str, Any]]:
        """Return the ``expanded-result`` or ``result`` list, whichever is present."""
        for key in ("expanded-result", "result"):
            records = body.get(key) if isinstance(body, dict) else None
            if isinstance(records, list):
                return [record for record in records if isinstance(record, dict)]
        return []

    def item(self, body: Any) -> dict[str, Any]:
        """Return the record itself; ORCID single routes are unwrapped."""
        return body if isinstance(body, dict) else {}

    def total(self, body: Any) -> int | None:
        """Return ``num-found``, or ``None`` when absent."""
        total = body.get("num-found") if isinstance(body, dict) else None
        if isinstance(total, int) and not isinstance(total, bool):
            return total
        return None

    def next_cursor(self, body: Any) -> str | None:
        """Return ``None``; ORCID pages by ``start`` offset only.

        ``body`` is unused; ORCID has no cursor paging.
        """
        return None

    def meta(self, body: Any) -> dict[str, Any]:
        """Return the envelope minus the result list."""
        if not isinstance(body, dict):
            return {}
        return {
            key: value
            for key, value in body.items()
            if key not in ("expanded-result", "result")
        }


__all__ = ["OrchisUnwrapper"]
