"""Shared fixtures and payload builders used by both test variants.

Settings are built with every relevant field explicit (and ``_env_file=None``)
so the suite never depends on the developer's shell or ``.env``. The variant
``client`` fixtures live in ``tests/_async/conftest.py`` (and its generated
``tests/_sync`` twin).
"""

import json
from pathlib import Path

import pytest
from dataphora import DataphoraSettings

BASE_URL = "https://api.datacite.org"
FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    """Load a trimmed real-API payload from ``tests/fixtures``."""
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture
def settings():
    """Fast, deterministic settings: no throttle, no retries."""
    return DataphoraSettings(
        _env_file=None,
        max_requests_per_second=1_000_000.0,
        max_concurrency=5,
        max_retries=0,
        max_retry_wait=0.05,
        timeout=5.0,
    )


def envelope(
    records: list, *, total: int | None = None, next_number: int | None = None
) -> dict:
    """Build a JSON:API list envelope the way DataCite sends it.

    ``links.next`` carries ``page[number]`` when the caller passes
    ``next_number``; cursor responses are built with ``cursor_envelope``.
    """
    return {
        "data": records,
        "meta": {
            "total": len(records) if total is None else total,
            "totalPages": 10000,
            "page": 1,
        },
        "links": {
            "self": f"{BASE_URL}/dois",
            "next": (
                f"{BASE_URL}/dois?page%5Bnumber%5D={next_number}"
                if next_number is not None
                else None
            ),
        },
    }


def cursor_envelope(records: list, *, total: int, next_cursor: str | None) -> dict:
    """Build a JSON:API list envelope with cursor paging links."""
    links: dict = {"self": f"{BASE_URL}/dois?page%5Bcursor%5D=1"}
    if next_cursor is not None:
        links["next"] = (
            f"{BASE_URL}/dois?page%5Bcursor%5D={next_cursor}&page%5Bsize%5D=1000"
        )
    return {
        "data": records,
        "meta": {"total": total, "totalPages": total},
        "links": links,
    }


def doi_resource(doi: str = "10.5438/0012", **attributes) -> dict:
    """Minimal raw JSON:API DOI record that validates against the model."""
    attributes.setdefault("doi", doi)
    attributes.setdefault("state", "findable")
    return {"id": doi, "type": "dois", "attributes": attributes}


def plain_resource(resource_id: str | int, type_name: str, **attributes) -> dict:
    """Minimal raw JSON:API resource record for the account families."""
    return {"id": resource_id, "type": type_name, "attributes": attributes}
