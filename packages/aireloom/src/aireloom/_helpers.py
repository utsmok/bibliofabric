"""Internal helpers for computed field derivation across AIREloom models."""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models.base import Pid, TypedPid

# ORCID pattern: 4 groups of 4 digits separated by hyphens, optionally with
# a check digit (0-9 or X).
_ORCID_RE = re.compile(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]")


def extract_pid_by_scheme(pids: Sequence[Pid], scheme: str) -> str | None:
    """Return the value of the first PID matching *scheme* (case-insensitive)."""
    target = scheme.lower()
    for pid in pids:
        s = pid.scheme.lower() if pid.scheme else ""
        if s == target and pid.value:
            return pid.value
    return None


def extract_all_pids_by_scheme(pids: Sequence[Pid], scheme: str) -> list[str]:
    """Return all PID values matching *scheme* (case-insensitive)."""
    target = scheme.lower()
    results: list[str] = []
    for pid in pids:
        s = pid.scheme.lower() if pid.scheme else ""
        if s == target and pid.value:
            results.append(pid.value)
    return results


def extract_orcid(
    original_ids: Sequence[str] | None,
    entity_id: str | None,
    pids: Sequence[TypedPid] | None = None,
) -> str | None:
    """Extract an ORCID from ``originalId``, ``pid``, or an OpenAIRE entity ID.

    OpenAIRE person IDs sometimes look like ``orcid_______::0000-0002-...``.
    The ``originalId`` list may contain bare ORCID strings, and ``pid`` entries
    carry ``{"typeCode": "orcid", "value": "0000-0002-..."}``.
    """
    if original_ids:
        for oid in original_ids:
            m = _ORCID_RE.search(oid)
            if m:
                return m.group(0)
    if pids:
        for entry in pids:
            if entry.typeCode.lower() == "orcid" and entry.value:
                m = _ORCID_RE.search(entry.value)
                if m:
                    return m.group(0)
    if entity_id and entity_id.startswith("orcid_______::"):
        candidate = entity_id.removeprefix("orcid_______::")
        m = _ORCID_RE.search(candidate)
        if m:
            return m.group(0)
    return None
