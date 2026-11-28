"""Shared fixtures and payload builders used by both test variants.

Settings are built with every relevant field explicit (and ``_env_file=None``)
so the suite never depends on the developer's shell or ``.env``. The variant
``client`` fixtures live in ``tests/_async/conftest.py`` (and its generated
``tests/_sync`` twin).
"""

import json
from pathlib import Path

import pytest
from diurnalia import DiurnaliaSettings

BASE_URL = "https://doaj.org/api/v4"
FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    """Load a trimmed real-API payload from ``tests/fixtures``."""
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture
def settings():
    """Fast, deterministic settings: no throttle, no retries."""
    return DiurnaliaSettings(
        _env_file=None,
        max_requests_per_second=1_000_000.0,
        max_concurrency=5,
        max_retries=0,
        max_retry_wait=0.05,
        timeout=5.0,
    )


def envelope(
    records: list, *, total: int | None = None, page: int = 1, page_size: int = 10
) -> dict:
    """Build a DOAJ search envelope."""
    return {
        "total": len(records) if total is None else total,
        "page": page,
        "pageSize": page_size,
        "timestamp": "2026-11-27T12:00:00.000000Z",
        "query": "*",
        "results": records,
    }


def journal(record_id: str, *, issn: str = "1932-6203", **fields) -> dict:
    """Minimal journal record that validates against the model."""
    record = {
        "id": record_id,
        "bibjson": {
            "title": f"Journal {record_id}",
            "eissn": issn,
            "publisher": {"name": "Example Publisher", "country": "NL"},
        },
        "created_date": "2013-01-01T00:00:00Z",
        "last_updated": "2026-09-01T00:00:00Z",
    }
    record.update(fields)
    return record


def article(record_id: str, *, doi: str = "10.3389/fpubh.2020.00115", **fields) -> dict:
    """Minimal article record that validates against the model."""
    record = {
        "id": record_id,
        "bibjson": {
            "title": f"Article {record_id}",
            "identifier": [
                {"id": "2296-2565", "type": "eissn"},
                {"id": doi, "type": "doi"},
            ],
            "journal": {"title": "Frontiers in Public Health", "issns": ["2296-2565"]},
            "year": "2020",
        },
        "created_date": "2020-04-01T00:00:00Z",
        "last_updated": "2026-09-01T00:00:00Z",
    }
    record.update(fields)
    return record
