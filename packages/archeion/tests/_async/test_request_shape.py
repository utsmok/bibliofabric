"""Outgoing request shape, paging, id lookups, and guards."""

import pytest
from archeion import ConfigurationError, NotFoundError

from ..conftest import entry, feed, load_fixture

TWO = load_fixture("two_entries.xml")


def params(request) -> dict[str, str]:
    return dict(request.url.params)


async def test_search_sends_query_sort_and_paging(client, httpx_mock):
    httpx_mock.add_response(text=feed(entry("2003.04590v2"), total=1))
    page = await client.query.search(
        "au:hickey AND cat:cs.DL",
        sort_by="submittedDate",
        sort_order="descending",
        start=20,
        page_size=10,
    )
    request = httpx_mock.get_requests()[-1]
    assert request.url.path == "/api/query"
    assert request.headers["accept"] == "application/atom+xml"
    assert params(request) == {
        "search_query": "au:hickey AND cat:cs.DL",
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "start": "20",
        "max_results": "10",
    }
    assert page.total == 1
    assert page.page == 3
    assert page.results[0].versioned_id == "2003.04590v2"


async def test_get_normalizes_the_id_and_raises_on_an_empty_feed(client, httpx_mock):
    httpx_mock.add_response(text=TWO)
    record = await client.query.get("arXiv:1706.03762")
    assert params(httpx_mock.get_requests()[-1])["id_list"] == "1706.03762"
    assert record.versioned_id is not None
    httpx_mock.add_response(text=feed(total=0))
    with pytest.raises(NotFoundError):
        await client.query.get("9999.99999")


async def test_batch_get_maps_entries_back_to_the_requested_ids(client, httpx_mock):
    httpx_mock.add_response(text=TWO)
    found = await client.query.batch_get(
        ["https://arxiv.org/abs/1706.03762v7", "hep-th/9711200", "2501.00001"]
    )
    request = httpx_mock.get_requests()[-1]
    assert params(request)["id_list"] == "1706.03762v7,hep-th/9711200,2501.00001"
    assert params(request)["max_results"] == "3"
    assert found["1706.03762v7"].title == "Attention Is All You Need"
    assert found["hep-th/9711200"].version == 3
    assert "2501.00001" not in found


async def test_old_style_id_with_version_is_rejected_before_sending(client):
    # arXiv answers HTTP 500 for these (verified 2026-11-28).
    with pytest.raises(ConfigurationError, match="hep-th/9711200v1"):
        await client.query.get("hep-th/9711200v1")


async def test_iterate_pages_until_the_total(client, httpx_mock):
    httpx_mock.add_response(text=feed(entry("1v1") + entry("2v1"), total=3))
    httpx_mock.add_response(text=feed(entry("3v1"), total=3, start=2))
    ids = [
        record.versioned_id
        async for record in client.query.iterate("all:x", page_size=2)
    ]
    assert ids == ["1v1", "2v1", "3v1"]
    starts = [params(request)["start"] for request in httpx_mock.get_requests()]
    assert starts == ["0", "2"]


async def test_iterate_stops_at_the_limit(client, httpx_mock):
    httpx_mock.add_response(text=feed(entry("1v1") + entry("2v1"), total=50))
    ids = [r.versioned_id async for r in client.query.iterate("all:x", limit=2)]
    assert ids == ["1v1", "2v1"]
    assert params(httpx_mock.get_requests()[-1])["max_results"] == "2"


async def test_count_reads_the_total_with_one_result(client, httpx_mock):
    httpx_mock.add_response(text=feed(entry("1v1"), total=189477))
    assert await client.query.count("all:electron") == 189477
    assert params(httpx_mock.get_requests()[-1])["max_results"] == "1"


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"query": "all:x", "page_size": 0},
        {"query": "all:x", "page_size": 2001},
        {"query": "all:x", "start": 29_995, "page_size": 10},
        {"query": "all:x", "sort_by": "citations"},
        {"query": "all:x", "sort_order": "up"},
    ],
)
async def test_guards_reject_bad_arguments(client, kwargs):
    with pytest.raises(ConfigurationError):
        await client.query.search(**kwargs)
