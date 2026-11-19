"""Shared fixtures: a client with the pacing gate disabled, and probe fixtures."""

import json
from pathlib import Path

import pytest
from stavrophora import StavrophoraClient, StavrophoraSettings

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name: str) -> dict:
    """Load a trimmed real response body from ``tests/fixtures``."""
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture
def settings() -> StavrophoraSettings:
    # max_requests_per_second=None skips the pacing gate so mocked tests stay fast
    return StavrophoraSettings(
        mailto="tester@example.org", max_requests_per_second=None, max_concurrency=8
    )


@pytest.fixture
async def client(settings):
    async with StavrophoraClient(settings=settings) as client:
        yield client


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
