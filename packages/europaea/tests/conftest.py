"""Shared fixtures and payload builders used by both test variants.

Settings are built with every relevant field explicit (and ``_env_file=None``)
so the suite never depends on the developer's shell or ``.env``. The variant
``client`` fixtures live in ``tests/_async/conftest.py`` (and its generated
``tests/_sync`` twin).
"""

import json
from pathlib import Path

import pytest
from europaea import EuropaeaSettings

BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest"
ANNOTATIONS_BASE_URL = "https://www.ebi.ac.uk/europepmc/annotations_api"
GRIST_BASE_URL = "https://www.ebi.ac.uk/europepmc/GristAPI/rest/get"
FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    """Load a trimmed real-API payload from ``tests/fixtures``."""
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture
def settings():
    """Fast, deterministic settings: no throttle, no retries."""
    return EuropaeaSettings(
        _env_file=None,
        max_requests_per_second=1_000_000.0,
        max_concurrency=5,
        max_retries=0,
        max_retry_wait=0.05,
        timeout=5.0,
    )


def search_envelope(
    records: list,
    *,
    hit_count: int | None = None,
    next_cursor_mark: str | None = None,
    result_type: str = "core",
) -> dict:
    """Build a ``/search`` response envelope."""
    body: dict = {
        "version": "6.9",
        "hitCount": len(records) if hit_count is None else hit_count,
        "request": {
            "queryString": "cancer",
            "resultType": result_type,
            "cursorMark": "*",
            "pageSize": 25,
            "sort": "",
            "synonym": False,
        },
        "resultList": {"result": records},
    }
    if next_cursor_mark is not None:
        body["nextCursorMark"] = next_cursor_mark
    return body


def lite_record(record_id: str = "23903748", **fields) -> dict:
    """Minimal ``resultType=lite`` record that validates against the model."""
    record = {
        "id": record_id,
        "source": "MED",
        "pmid": record_id,
        "title": "Nanometre-scale thermometry in a living cell.",
        "authorString": "Kucsko G, Maurer PC.",
        "journalTitle": "Nature",
        "pubYear": "2013",
        "citedByCount": 452,
    }
    record.update(fields)
    return record


def core_record(record_id: str = "23903748", **fields) -> dict:
    """Minimal ``resultType=core`` record that validates against the model."""
    record = lite_record(
        record_id,
        isOpenAccess="Y",
        inEPMC="Y",
        journalInfo={
            "issue": "7460",
            "volume": "500",
            "yearOfPublication": 2013,
            "journal": {"title": "Nature", "issn": "0028-0836"},
        },
        authorList={
            "author": [
                {
                    "fullName": "Kucsko G",
                    "lastName": "Kucsko",
                    "initials": "G",
                    "authorId": {"type": "ORCID", "value": "0000-0002-4189-3154"},
                }
            ]
        },
        keywordList={"keyword": ["nanodiamond", "thermometry"]},
    )
    record.update(fields)
    return record


def list_envelope(
    records: list,
    *,
    wrapper: str = "referenceList",
    item: str = "reference",
    hit_count: int | None = None,
    page: int = 1,
    page_size: int = 25,
) -> dict:
    """Build a paged per-article envelope (references, citations, links)."""
    return {
        "version": "6.9",
        "hitCount": len(records) if hit_count is None else hit_count,
        "request": {
            "id": "23903748",
            "source": "MED",
            "offSet": page,
            "pageSize": page_size,
        },
        wrapper: {item: records},
    }


def citation_record(record_id: str = "21574616", **fields) -> dict:
    """Minimal reference/citation record that validates against the model."""
    record = {
        "id": record_id,
        "source": "MED",
        "citationType": "JOURNAL ARTICLE",
        "title": "Quantum dot nano thermometers.",
        "authorString": "Yang JM.",
        "journalAbbreviation": "ACS Nano",
        "pubYear": 2011,
        "citedByCount": 0,
    }
    record.update(fields)
    return record


def article_annotation(record_id: str = "23903748", **fields) -> dict:
    """Minimal ``annotationsByArticleIds`` element that validates."""
    record = {
        "source": "MED",
        "extId": record_id,
        "pmcid": "PMC4221854",
        "annotations": [
            {
                "prefix": "spin associated with",
                "exact": "nitrogen",
                "postfix": "-vacancy colour centres in",
                "tags": [
                    {
                        "name": "nitrogen",
                        "uri": "http://purl.obolibrary.org/obo/CHEBI_51143",
                    }
                ],
                "id": f"http://europepmc.org/article/MED/{record_id}#europepmc-abc",
                "type": "Chemicals",
            }
        ],
    }
    record.update(fields)
    return record


def annotation_page(**fields) -> dict:
    """Build a cursor-paged annotations envelope."""
    page: dict = {
        "cursorMark": 0.0,
        "nextCursorMark": 265.731278071,
        "articles": [article_annotation()],
    }
    page.update(fields)
    return page


def grist_envelope(records: list | None = None, *, hit_count: str = "1739") -> dict:
    """Build a Grist answer envelope."""
    if records is None:
        records = [
            {
                "Person": {
                    "FamilyName": "Asante",
                    "GivenName": "Kwaku",
                    "Initials": "KP",
                    "Title": "Dr",
                },
                "Grant": {
                    "Funder": {
                        "Name": "Wellcome Trust",
                        "pubMedSearchTerm": "Wellcome Trust",
                    },
                    "Id": "329783",
                    "Title": "Predictive Modeling for climate-sensitive health outcomes",
                },
            }
        ]
    return {
        "HitCount": hit_count,
        "Request": {"Query": "malaria", "ResultType": "Lite", "Page": "1"},
        "RecordList": {"Record": records},
    }
