"""Journals helpers: the DOI-per-year breakdown."""

from tests.conftest import fixture


async def test_dois_by_year_parses_the_breakdown_pairs(httpx_mock, client):
    httpx_mock.add_response(json=fixture("journal_get.json"))
    counts = await client.journals.dois_by_year("20493630")
    assert httpx_mock.get_requests()[0].url.path == "/v1/journals/2049-3630"
    expected = {
        int(year): count
        for year, count in fixture("journal_get.json")["message"]["breakdowns"][
            "dois-by-issued-year"
        ]
    }
    assert counts == expected
    assert all(type(year) is int for year in counts)


async def test_dois_by_year_is_empty_without_breakdowns(httpx_mock, client):
    httpx_mock.add_response(
        json={
            "status": "ok",
            "message-type": "journal",
            "message": {"title": "Some Journal", "ISSN": ["2049-3630"]},
        }
    )
    assert await client.journals.dois_by_year("20493630") == {}
