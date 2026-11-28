"""Shared fixtures and payload builders used by both test variants.

Settings are built with every relevant field explicit (and ``_env_file=None``)
so the suite never depends on the developer's shell or ``.env``. The variant
``client`` fixtures live in ``tests/_async/conftest.py`` (and its generated
``tests/_sync`` twin).
"""

import json
from pathlib import Path

import pytest
from quiddita import QuidditaSettings

BASE_URL = "https://www.wikidata.org"
FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    """Load a trimmed real-API payload from ``tests/fixtures``."""
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture
def settings():
    """Fast, deterministic settings: no throttle, no retries."""
    return QuidditaSettings(
        _env_file=None,
        max_requests_per_second=1_000_000.0,
        max_concurrency=5,
        max_retries=0,
        max_retry_wait=0.05,
        timeout=5.0,
    )


def entity(entity_id: str = "Q42", **fields) -> dict:
    """Minimal entity record that validates against the model."""
    record = {
        "type": "item",
        "id": entity_id,
        "labels": {"en": {"language": "en", "value": "Douglas Adams"}},
        "descriptions": {},
        "aliases": {},
        "claims": {},
        "sitelinks": {},
    }
    record.update(fields)
    return record


def entities_envelope(*records: dict) -> dict:
    """Build a ``wbgetentities`` envelope keyed by entity id."""
    return {
        "entities": {record["id"]: record for record in records},
        "success": 1,
    }


def search_result(result_id: str, label: str, **fields) -> dict:
    """Minimal ``wbsearchentities`` hit."""
    record = {
        "id": result_id,
        "label": label,
        "description": "a result",
        "match": {"type": "label", "language": "en", "text": label},
    }
    record.update(fields)
    return record


def search_envelope(results: list[dict], offset: int = 0) -> dict:
    """Build a ``wbsearchentities`` envelope."""
    return {"searchinfo": {"search": "x", "offset": offset}, "search": results}


def claim_record(property_id: str = "P31", value_id: str = "Q5") -> dict:
    """Minimal claim with one value snak."""
    return {
        "mainsnak": {
            "snaktype": "value",
            "property": property_id,
            "hash": "0" * 40,
            "datavalue": {
                "value": {"entity-type": "item", "numeric-id": int(value_id[1:])},
                "type": "wikibase-entityid",
            },
            "datatype": "wikibase-item",
        },
        "type": "statement",
        "rank": "normal",
    }


def rest_statement(statement_id: str, property_id: str, content: str) -> dict:
    """Minimal REST statement."""
    return {
        "id": statement_id,
        "rank": "normal",
        "property": property_id,
        "value": {"type": "value", "content": content},
        "qualifiers": [],
        "references": [],
    }


def rest_item(item_id: str = "Q42", **fields) -> dict:
    """Minimal REST item record."""
    record = {
        "id": item_id,
        "type": "item",
        "labels": {"en": "Douglas Adams"},
        "descriptions": {},
        "aliases": {},
        "statements": {},
        "sitelinks": {},
    }
    record.update(fields)
    return record


def sparql_envelope(rows: list[dict]) -> dict:
    """Build a SPARQL 1.1 JSON result for one variable ``item``."""
    return {
        "head": {"vars": ["item"]},
        "results": {"bindings": rows},
    }
