"""End-to-end HTTP integration tests using pytest-httpx.

These exercise the full stack — real StavrophoraClient, real httpx transport
mocked by pytest-httpx, real unwrapping — not just the resource clients.
"""

import httpx
import pytest
from pytest_httpx import HTTPXMock

from stavrophora import StavrophoraClient, Work

WORK = {
    "DOI": "10.1038/nature12373",
    "title": ["Nanometre-scale thermometry in a living cell"],
    "type": "journal-article",
    "is-referenced-by-count": 500,
}

SEARCH = {
    "status": "ok",
    "message-type": "work-list",
    "message": {"total-results": 1, "items": [WORK]},
}


@pytest.fixture
def client():
    return StavrophoraClient(mailto="test@example.org")


@pytest.mark.asyncio
async def test_get_work_full_stack(client, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=httpx.URL(
            "https://api.crossref.org/v1/works/10.1038/nature12373",
            params={"mailto": "test@example.org"},
        ),
        json={"status": "ok", "message": WORK},
    )
    work = await client.works.get("10.1038/nature12373")
    assert isinstance(work, Work)
    assert work.doi == "10.1038/nature12373"
    request = httpx_mock.get_requests()[0]
    assert "mailto=test%40example.org" in str(request.url)


@pytest.mark.asyncio
async def test_search_works_full_stack(client, httpx_mock: HTTPXMock):
    expected_params = {
        "filter": "type:journal-article",
        "sort": "is-referenced-by-count",
        "order": "desc",
        "select": "DOI,title",
        "offset": "0",
        "rows": "5",
        "mailto": "test@example.org",
    }
    httpx_mock.add_response(
        url=httpx.URL("https://api.crossref.org/v1/works", params=expected_params),
        json=SEARCH,
    )
    response = await client.works.search(
        filters={"type": "journal-article"},
        page_size=5,
        sort_by="is-referenced-by-count:desc",
        select=["DOI", "title"],
    )
    assert response.message.total_results == 1
    assert response.message.items[0].is_referenced_by_count == 500
    request = httpx_mock.get_requests()[0]
    query = str(request.url.params)
    assert "filter=type%3Ajournal-article" in query
    assert "sort=is-referenced-by-count" in query
    assert "order=desc" in query
    assert "select=DOI%2Ctitle" in query
    assert "rows=5" in query
    assert "offset=0" in query
    assert "page" not in query


@pytest.mark.asyncio
async def test_cursor_iteration_full_stack(client, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=httpx.URL(
            "https://api.crossref.org/v1/works",
            params={"cursor": "*", "rows": "2", "mailto": "test@example.org"},
        ),
        json={
            "message": {
                "total-results": 3,
                "next-cursor": "TWO",
                "items": [{"DOI": "10.1/a"}, {"DOI": "10.1/b"}],
            }
        },
    )
    httpx_mock.add_response(
        url=httpx.URL(
            "https://api.crossref.org/v1/works",
            params={"cursor": "TWO", "rows": "2", "mailto": "test@example.org"},
        ),
        json={"message": {"total-results": 3, "items": []}},
    )
    dois = [w.doi async for w in client.works.iterate(page_size=2)]
    assert dois == ["10.1/a", "10.1/b"]


@pytest.mark.asyncio
async def test_404_raises_api_error(client, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=httpx.URL(
            "https://api.crossref.org/v1/works/10.9999/nope",
            params={"mailto": "test@example.org"},
        ),
        status_code=404,
        json={"status": "error"},
    )
    from bibliofabric.exceptions import APIError

    with pytest.raises(APIError):
        await client.works.get("10.9999/nope")
