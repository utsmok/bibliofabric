"""Internal helpers for computed field derivation across AIREloom models."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models.research_product import Pid

# ORCID pattern: 4 groups of 4 digits separated by hyphens, optionally with
# a check digit (0-9 or X).
_ORCID_RE = re.compile(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]")


def extract_pid_by_scheme(pids: list[Pid], scheme: str) -> str | None:
    """Return the value of the first PID matching *scheme* (case-insensitive).

    Handles both the typed ``Pid`` model and raw dicts from
    ``__pydantic_extra__`` or unstructured API data.
    """
    target = scheme.lower()
    for pid in pids:
        # Typed Pid model
        s = pid.scheme.lower() if pid.scheme else ""
        if s == target and pid.value:
            return pid.value
        # Also check __pydantic_extra__ for nested pid dicts
        extra = getattr(pid, "__pydantic_extra__", None)
        if extra and isinstance(extra, dict):
            es = extra.get("scheme", "")
            ev = extra.get("value", "")
            if isinstance(es, str) and es.lower() == target and ev:
                return str(ev)
    return None


def extract_all_pids_by_scheme(pids: list[Pid], scheme: str) -> list[str]:
    """Return all PID values matching *scheme* (case-insensitive)."""
    target = scheme.lower()
    results: list[str] = []
    for pid in pids:
        s = pid.scheme.lower() if pid.scheme else ""
        if s == target and pid.value:
            results.append(pid.value)
    return results


def extract_orcid(original_ids: list[str] | None, entity_id: str | None) -> str | None:
    """Extract an ORCID from ``originalId`` list or from an OpenAIRE entity ID.

    OpenAIRE person IDs sometimes look like ``orcid_______::0000-0002-...``.
    The ``originalId`` list may contain bare ORCID strings.
    """
    if original_ids:
        for oid in original_ids:
            m = _ORCID_RE.search(oid)
            if m:
                return m.group(0)
    if entity_id and entity_id.startswith("orcid_______::"):
        candidate = entity_id.removeprefix("orcid_______::")
        m = _ORCID_RE.search(candidate)
        if m:
            return m.group(0)
    return None
