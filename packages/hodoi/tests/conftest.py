"""Shared fixtures used by both test variants.

Settings are built with every relevant field explicit (and ``_env_file=None``)
so the suite never depends on the developer's shell or ``.env``. The variant
``client`` fixtures live in ``tests/_async/conftest.py`` (and its generated
``tests/_sync`` twin).
"""

import json
from pathlib import Path

import pytest
from hodoi import HodoiSettings

BASE_URL = "https://doi.org"
FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict | list | str:
    """Load a trimmed real-API payload from ``tests/fixtures``."""
    text = (FIXTURES / name).read_text()
    if name.endswith(".json"):
        return json.loads(text)
    return text


@pytest.fixture
def settings():
    """Fast, deterministic settings: no throttle, no retries."""
    return HodoiSettings(
        _env_file=None,
        max_requests_per_second=1_000_000.0,
        max_concurrency=5,
        max_retries=0,
        max_retry_wait=0.05,
        timeout=5.0,
    )
