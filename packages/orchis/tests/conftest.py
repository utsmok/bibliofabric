"""Shared fixtures and payload builders used by both test variants.

Settings are built with every relevant field explicit (and ``_env_file=None``)
so the suite never depends on the developer's shell or ``.env``. The variant
``client`` fixtures live in ``tests/_async/conftest.py`` (and its generated
``tests/_sync`` twin).
"""

import json
from pathlib import Path

import pytest
from orchis import OrchisSettings

ORCID_ID = "0000-0002-1694-233X"
BASE_URL = "https://pub.orcid.org/v3.0"
FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    """Load a trimmed real-API payload from ``tests/fixtures``."""
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture
def settings():
    """Fast, deterministic settings: no throttle, no retries, no token."""
    return OrchisSettings(
        _env_file=None,
        access_token=None,
        max_requests_per_second=1_000_000.0,
        max_concurrency=5,
        max_retries=0,
        max_retry_wait=0.05,
        timeout=5.0,
    )


def expanded_envelope(records: list[dict], *, num_found: int | None = None) -> dict:
    """Build an ``/expanded-search`` envelope."""
    return {
        "expanded-result": records,
        "num-found": len(records) if num_found is None else num_found,
    }


def solr_envelope(records: list[dict], *, num_found: int | None = None) -> dict:
    """Build a ``/search`` envelope."""
    return {
        "result": records,
        "num-found": len(records) if num_found is None else num_found,
    }


def expanded_result(orcid_id: str, **fields) -> dict:
    """Minimal expanded-search result that validates against the model."""
    record = {
        "orcid-id": orcid_id,
        "given-names": "Georg",
        "family-names": "Kucsko",
        "credit-name": None,
        "other-name": [],
        "email": [],
        "institution-name": ["Harvard University"],
    }
    record.update(fields)
    return record


def solr_result(orcid_id: str) -> dict:
    """Minimal Solr search result."""
    return {
        "orcid-identifier": {
            "uri": f"https://orcid.org/{orcid_id}",
            "path": orcid_id,
            "host": "orcid.org",
        }
    }
