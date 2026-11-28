"""Shared fixtures and payload builders used by both test variants.

Settings are built with every relevant field explicit (and ``_env_file=None``)
so the suite never depends on the developer's shell or ``.env``. The variant
``client`` fixtures live in ``tests/_async/conftest.py`` (and its generated
``tests/_sync`` twin).
"""

import json
from pathlib import Path

import pytest
from opcitato import OpcitatoSettings

BASE_URL = "https://api.opencitations.net"
FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> str:
    """Load a trimmed real-API payload from ``tests/fixtures`` as text."""
    return (FIXTURES / name).read_text()


def load_fixture_json(name: str) -> list:
    """Load a trimmed real-API payload from ``tests/fixtures`` as JSON."""
    return json.loads(load_fixture(name))


@pytest.fixture
def settings():
    """Fast, deterministic settings: no throttle, no retries."""
    return OpcitatoSettings(
        _env_file=None,
        max_requests_per_second=1_000_000.0,
        max_concurrency=5,
        max_retries=0,
        max_retry_wait=0.05,
        timeout=5.0,
    )


def citation(**fields) -> dict:
    """Minimal citation row that validates against the model."""
    row = {
        "oci": "06101801781-06180334099",
        "citing": "omid:br/06101801781 doi:10.7717/peerj-cs.421 pmid:33817056",
        "cited": "omid:br/06180334099 doi:10.1108/jd-12-2013-0166",
        "creation": "2021-03-10",
        "timespan": "P6Y0M1D",
        "journal_sc": "no",
        "author_sc": "no",
    }
    row.update(fields)
    return row


def metadata_row(**fields) -> dict:
    """Minimal Meta metadata row that validates against the model."""
    row = {
        "id": "doi:10.1108/jd-12-2013-0166 omid:br/06180334099",
        "title": "Setting Our Bibliographic References Free",
        "author": "Peroni, Silvio [orcid:0000-0003-0530-4305]",
        "editor": "",
        "pub_date": "2015-03-09",
        "issue": "2",
        "volume": "71",
        "venue": "Journal Of Documentation [issn:0022-0418]",
        "page": "253-277",
        "type": "journal article",
        "publisher": "Emerald [crossref:140]",
    }
    row.update(fields)
    return row


def count_rows(number: int) -> list[dict]:
    """Build the one-row list a count operation returns."""
    return [{"count": str(number)}]
