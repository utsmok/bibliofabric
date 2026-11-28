"""Shared fixtures and payload builders used by both test variants.

Settings are built with every relevant field explicit (and ``_env_file=None``)
so the suite never depends on the developer's shell or ``.env``. The variant
``client`` fixtures live in ``tests/_async/conftest.py`` (and its generated
``tests/_sync`` twin).
"""

import json
from pathlib import Path
from typing import Any

import pytest
from scholiast import ScholiastSettings

GRAPH_BASE_URL = "https://api.semanticscholar.org/graph/v1"
FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> Any:
    """Load a trimmed real-API payload from ``tests/fixtures``."""
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture
def settings():
    """Fast, deterministic settings: no throttle, no retries, no key."""
    return ScholiastSettings(
        _env_file=None,
        api_key=None,
        max_requests_per_second=1_000_000.0,
        max_concurrency=5,
        max_retries=0,
        max_retry_wait=0.05,
        timeout=5.0,
    )


def paper(paper_id: str, **fields) -> dict:
    """Minimal paper record that validates against the model."""
    record = {"paperId": paper_id, "title": f"Paper {paper_id}", "year": 2024}
    record.update(fields)
    return record


def author(author_id: str, **fields) -> dict:
    """Minimal author record that validates against the model."""
    record = {"authorId": author_id, "name": f"Author {author_id}"}
    record.update(fields)
    return record


def search_envelope(records: list, **extra) -> dict:
    """Build a ``{total, offset, next, data}`` relevance-search envelope."""
    envelope = {
        "total": len(records),
        "offset": 0,
        "next": len(records) if records else None,
        "data": records,
    }
    envelope.update(extra)
    return envelope


def list_envelope(records: list, **extra) -> dict:
    """Build a ``{data, next, offset}`` sub-list envelope (citations, papers)."""
    envelope: dict = {"data": records, "offset": 0}
    if records:
        envelope["next"] = len(records)
    envelope.update(extra)
    return envelope
