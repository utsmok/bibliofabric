"""Shared fixtures and payload builders used by both test variants.

Settings are built with every relevant field explicit (and ``_env_file=None``)
so the suite never depends on the developer's shell or ``.env``. The variant
``client`` fixtures live in ``tests/_async/conftest.py`` (and its generated
``tests/_sync`` twin).
"""

import json
from pathlib import Path

import pytest
from seriatim import SeriatimSettings

BASE_URL = "https://portal.issn.org"
FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> str:
    """Load one fixture file from ``tests/fixtures`` as text."""
    return (FIXTURES / name).read_text(encoding="utf-8")


def load_json_fixture(name: str) -> dict:
    """Load one JSON fixture from ``tests/fixtures``."""
    return json.loads(load_fixture(name))


@pytest.fixture
def settings():
    """Fast, deterministic settings: no throttle, no retries."""
    return SeriatimSettings(
        _env_file=None,
        max_requests_per_second=1_000_000.0,
        max_concurrency=5,
        max_retries=0,
        max_retry_wait=0.05,
        timeout=5.0,
    )
