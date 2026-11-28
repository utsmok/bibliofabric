"""Shared fixtures used by both test variants.

Settings are built with every relevant field explicit (and ``_env_file=None``)
so the suite never depends on the developer's shell or ``.env``. The JSON
fixtures are trimmed real API answers of 2026-11-28.
"""

import json
from pathlib import Path
from typing import Any

import pytest
from prodromus import ProdromusSettings

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> Any:
    """Load a trimmed real-API answer from ``tests/fixtures``."""
    return json.loads((FIXTURES / name).read_text())


def envelope(records: list, *, cursor: int, count: int, total: int) -> dict:
    """Build a paged ``details`` envelope.

    Like the live API, the first page sends ``cursor`` as a number and later
    pages send it as a string.
    """
    return {
        "messages": [
            {
                "status": "ok",
                "cursor": cursor if cursor == 0 else str(cursor),
                "count": count,
                "total": str(total),
            }
        ],
        "collection": records,
    }


@pytest.fixture
def settings():
    """Fast, deterministic settings: no throttle, no retries."""
    return ProdromusSettings(
        _env_file=None,
        max_requests_per_second=1_000_000.0,
        max_concurrency=5,
        max_retries=0,
        max_retry_wait=0.05,
        timeout=5.0,
    )
