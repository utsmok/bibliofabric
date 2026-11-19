"""Shared payload builders and fixture bodies used by both test variants."""

import json
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name: str) -> dict:
    """Load a trimmed real response body from ``tests/fixtures``."""
    return json.loads((FIXTURES / name).read_text())


def works_envelope(items: list[dict], **message: object) -> dict:
    """Build a minimal Crossref list envelope around the given items."""
    message.setdefault("total-results", len(items))
    return {
        "status": "ok",
        "message-type": "work-list",
        "message": {"items": items, **message},
    }


def work(doi: str) -> dict:
    """Minimal work record that parses into ``Work``."""
    return {"DOI": doi, "title": [f"Work {doi}"], "type": "journal-article"}
