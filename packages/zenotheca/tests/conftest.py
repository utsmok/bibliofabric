"""Shared fixtures and payload builders used by both test variants.

Settings are built with every relevant field explicit (and ``_env_file=None``)
so the suite never depends on the developer's shell or ``.env``. The variant
``client`` fixtures live in ``tests/_async/conftest.py`` (and its generated
``tests/_sync`` twin).
"""

import json
from pathlib import Path

import pytest
from zenotheca import ZenothecaSettings

BASE_URL = "https://zenodo.org/api"
FIXTURES = Path(__file__).parent / "fixtures"

RECORD_ID = 24378467
CONCEPT_ID = "6347574"
OLD_RECORD_ID = 5534443
COMMUNITY_SLUG = "ror-data"


def load_fixture(name: str) -> dict:
    """Load a trimmed real-API payload from ``tests/fixtures``."""
    return json.loads((FIXTURES / name).read_text())


def load_text(name: str) -> str:
    """Load a trimmed real-API XML fixture from ``tests/fixtures``."""
    return (FIXTURES / name).read_text()


VOCAB_NAME = "resourcetypes"


def vocab_entry(entry_id: str = "publication", **fields) -> dict:
    """Minimal vocabulary entry payload that validates against the model."""
    payload = {
        "id": entry_id,
        "revision_id": 1,
        "created": "2020-01-01T00:00:00+00:00",
        "updated": "2020-01-01T00:00:00+00:00",
        "title": {"en": "Publication"},
        "type": VOCAB_NAME,
        "links": {
            "self": f"https://zenodo.org/api/vocabularies/{VOCAB_NAME}/{entry_id}"
        },
    }
    payload.update(fields)
    return payload


def vocab_envelope(entries: list, *, total: int | None = None, **extra) -> dict:
    """A vocabulary hits envelope like the ones the API answers."""
    hits: dict = {"hits": entries}
    if total is not None:
        hits["total"] = total
    body = {"hits": hits, "links": {}}
    body.update(extra)
    return body


@pytest.fixture
def settings():
    """Fast, deterministic settings: no throttle, no retries."""
    return ZenothecaSettings(
        _env_file=None,
        api_token=None,
        max_requests_per_second=1_000_000.0,
        max_concurrency=5,
        max_retries=0,
        max_retry_wait=0.05,
        timeout=5.0,
    )


def record(record_id: int = RECORD_ID, **fields) -> dict:
    """Minimal record payload that validates against the model."""
    payload = load_fixture("record.json")
    payload.update(fields)
    payload["id"] = record_id
    payload["recid"] = str(record_id)
    payload["links"] = {
        **payload["links"],
        "self": f"https://zenodo.org/api/records/{record_id}",
    }
    return payload


def old_record() -> dict:
    """A record from an older ROR data concept, for version listing."""
    return load_fixture("versions_page.json")["hits"]["hits"][0]


def envelope(records: list, *, total: int | None = None, **extra) -> dict:
    """Build a Zenodo search envelope."""
    return {
        "hits": {
            "hits": records,
            "total": len(records) if total is None else total,
        },
        "links": {},
        **extra,
    }


def community(slug: str = COMMUNITY_SLUG, **fields) -> dict:
    """Minimal community payload that validates against the model."""
    payload = load_fixture("community.json")
    payload.update(fields)
    payload["slug"] = slug
    return payload


def files_listing(record_id: int = RECORD_ID) -> dict:
    """A ``/records/{id}/files`` listing for ``record_id``."""
    listing = load_fixture("files_list.json")
    listing["links"] = {"self": f"https://zenodo.org/api/records/{record_id}/files"}
    for entry in listing["entries"]:
        entry["links"] = {
            name: value.replace(f"/{RECORD_ID}/", f"/{record_id}/")
            for name, value in entry["links"].items()
        }
    return listing
