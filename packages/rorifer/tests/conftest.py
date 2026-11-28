"""Shared fixtures and payload builders used by both test variants.

Settings are built with every relevant field explicit (and ``_env_file=None``)
so the suite never depends on the developer's shell or ``.env``. The variant
``client`` fixtures live in ``tests/_async/conftest.py`` (and its generated
``tests/_sync`` twin).
"""

import json
from pathlib import Path

import pytest
from rorifer import RoriferSettings

BASE_URL = "https://api.ror.org/v2"
FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    """Load a trimmed real-API payload from ``tests/fixtures``."""
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture
def settings():
    """Fast, deterministic settings: no throttle, no retries."""
    return RoriferSettings(
        _env_file=None,
        max_requests_per_second=1_000_000.0,
        max_concurrency=5,
        max_retries=0,
        max_retry_wait=0.05,
        timeout=5.0,
    )


def envelope(records: list, *, number_of_results: int | None = None) -> dict:
    """Build a ROR list/search envelope."""
    return {
        "items": records,
        "number_of_results": (
            len(records) if number_of_results is None else number_of_results
        ),
        "meta": {"types": [], "countries": [], "continents": [], "statuses": []},
    }


def organization(record_id: str, **fields) -> dict:
    """Minimal organization record that validates against the model."""
    record = {
        "id": f"https://ror.org/{record_id}",
        "names": [
            {"lang": None, "types": ["ror_display", "label"], "value": record_id}
        ],
        "types": ["education"],
        "status": "active",
        "domains": [],
        "links": [],
        "locations": [],
        "external_ids": [],
        "relationships": [],
        "admin": {
            "created": {"date": "2018-11-14", "schema_version": "1.0"},
            "last_modified": {"date": "2026-07-20", "schema_version": "2.1"},
        },
    }
    record.update(fields)
    return record
