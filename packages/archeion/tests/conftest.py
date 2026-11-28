"""Shared fixtures used by both test variants.

Settings are built with every relevant field explicit (and ``_env_file=None``)
so the suite never depends on the developer's shell or ``.env``. The variant
``client`` fixtures live in ``tests/_async/conftest.py`` (and its generated
``tests/_sync`` twin). The XML fixtures are real API answers of 2026-11-28.
"""

from pathlib import Path

import pytest
from archeion import ArcheionSettings

BASE_URL = "https://export.arxiv.org/api"
FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> str:
    """Load a real Atom feed from ``tests/fixtures``."""
    return (FIXTURES / name).read_text()


def feed(
    entries: str = "", *, total: int = 0, start: int = 0, per_page: int = 10
) -> str:
    """Build a minimal Atom feed around entry elements."""
    return (
        "<?xml version='1.0' encoding='UTF-8'?>"
        '<feed xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/" '
        'xmlns:arxiv="http://arxiv.org/schemas/atom" '
        'xmlns="http://www.w3.org/2005/Atom">'
        "<id>https://arxiv.org/api/test</id>"
        f"<opensearch:itemsPerPage>{per_page}</opensearch:itemsPerPage>"
        f"<opensearch:totalResults>{total}</opensearch:totalResults>"
        f"<opensearch:startIndex>{start}</opensearch:startIndex>"
        f"{entries}</feed>"
    )


def entry(arxiv_id: str, title: str = "A title") -> str:
    """Build one minimal entry element."""
    return (
        f"<entry><id>http://arxiv.org/abs/{arxiv_id}</id><title>{title}</title>"
        "<author><name>A. Author</name></author></entry>"
    )


@pytest.fixture
def settings():
    """Fast, deterministic settings: no throttle, no retries."""
    return ArcheionSettings(
        _env_file=None,
        max_requests_per_second=1_000_000.0,
        max_concurrency=5,
        max_retries=0,
        max_retry_wait=0.05,
        timeout=5.0,
    )
