"""Shared test fixtures for stavrophora tests."""

import pytest

from stavrophora.unwrapper import CrossrefUnwrapper


@pytest.fixture
def unwrapper():
    return CrossrefUnwrapper()


@pytest.fixture
def sample_work_json():
    return {
        "DOI": "10.1038/nature12373",
        "title": ["Nanometre-scale thermometry in a living cell"],
        "container-title": ["Nature"],
        "type": "journal-article",
        "publisher": "Springer Science and Business Media LLC",
        "issued": {"date-parts": [[2013, 7, 31]]},
        "is-referenced-by-count": 500,
        "ISSN": ["0028-0836", "1476-4687"],
        "subject": ["Science", "Nature and Landscape Ecology"],
        "author": [
            {
                "given": "G.",
                "family": "Kucsko",
                "orcid": "https://orcid.org/0000-0002-1234-5678",
                "affiliation": [{"name": "ETH Zurich"}],
                "sequence": "first",
                "authenticated-orcid": False,
            },
            {"name": "Scientific Collective", "sequence": "additional"},
        ],
        "license": [
            {
                "URL": "https://creativecommons.org/licenses/by/4.0/",
                "content-version": "vor",
                "delay": 0,
            }
        ],
        "funder": [
            {
                "name": "Swiss National Science Foundation",
                "DOI": "10.13039/501100001711",
                "award": ["123456"],
                "doi-asserted": True,
            }
        ],
        "reference-count": 50,
        "member": "298",
        "prefix": "10.1038",
        "edition-number": None,
        "assertion": None,
    }


@pytest.fixture
def sample_works_response(sample_work_json):
    return {
        "status": "ok",
        "message-type": "work-list",
        "message-version": "1.0.0",
        "message": {
            "query": {"search-terms": None, "start-index": 0},
            "total-results": 1,
            "items-per-page": 20,
            "items": [sample_work_json],
        },
    }
