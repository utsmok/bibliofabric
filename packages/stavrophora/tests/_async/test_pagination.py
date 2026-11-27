"""Cursor pagination over the Crossref envelope, resume, and count."""

import pytest
from bibliofabric.exceptions import ValidationError
from stavrophora import WorksFilters

from .conftest import fixture, work, works_envelope


async def test_iterate_walks_cursor_pages(httpx_mock, client):
    httpx_mock.add_response(json=fixture("cursor_p1.json"))
    httpx_mock.add_response(json=fixture("cursor_p2.json"))
    httpx_mock.add_response(json=works_envelope([]))
    checkpoints: list[tuple[int, str | None]] = []

    items = [
        item
        async for item in client.works.iterate(
            query="climate",
            on_page=lambda number, cursor: checkpoints.append((number, cursor)),
        )
    ]

    assert len(items) == 4
    assert items[0].doi == "10.1007/s002679900045"
    assert items[2].doi == "10.1007/s002679900131"
    assert checkpoints == [
        (1, fixture_page2_cursor()),
        (2, fixture_page3_cursor()),
        (3, None),
    ]
    requests = httpx_mock.get_requests()
    assert len(requests) == 3
    assert requests[0].url.params["cursor"] == "*"
    assert requests[1].url.params["cursor"] == fixture_page2_cursor()
    assert requests[2].url.params["cursor"] == fixture_page3_cursor()


def fixture_page2_cursor() -> str:
    return fixture("cursor_p1.json")["message"]["next-cursor"]


def fixture_page3_cursor() -> str:
    return fixture("cursor_p2.json")["message"]["next-cursor"]


async def test_iterate_defaults_to_1000_rows(httpx_mock, client):
    httpx_mock.add_response(json=works_envelope([]))
    [item async for item in client.works.iterate()]
    assert httpx_mock.get_requests()[0].url.params["rows"] == "1000"


async def test_iterate_repeats_all_parameters_on_each_page(httpx_mock, client):
    httpx_mock.add_response(json=fixture("cursor_p1.json"))
    httpx_mock.add_response(json=works_envelope([]))
    [
        item
        async for item in client.works.iterate(
            WorksFilters(type="dataset"), query="climate", select=["DOI"]
        )
    ]
    second = httpx_mock.get_requests()[1].url.params
    assert second["cursor"] == fixture_page2_cursor()
    assert second["filter"] == "type:dataset"
    assert second["query"] == "climate"
    assert second["select"] == "DOI"


async def test_iterate_resumes_from_a_saved_cursor(httpx_mock, client):
    httpx_mock.add_response(json=works_envelope([work("10.1/resumed")]))
    items = [
        item async for item in client.works.iterate(cursor="SAVED-CURSOR", limit=1)
    ]
    assert httpx_mock.get_requests()[0].url.params["cursor"] == "SAVED-CURSOR"
    assert [item.doi for item in items] == ["10.1/resumed"]


async def test_iterate_stops_at_limit(httpx_mock, client):
    httpx_mock.add_response(json=fixture("cursor_p1.json"))
    httpx_mock.add_response(json=fixture("cursor_p2.json"))
    items = [item async for item in client.works.iterate(limit=3)]
    assert len(items) == 3
    assert len(httpx_mock.get_requests()) == 2


async def test_count_requests_a_minimal_page(httpx_mock, client):
    httpx_mock.add_response(json=fixture("facet_archive.json"))
    total = await client.works.count(query="climate")
    request = httpx_mock.get_requests()[0]
    assert request.url.params["rows"] == "0"
    assert request.url.params["offset"] == "0"
    assert "cursor" not in request.url.params
    assert total == 641402


@pytest.mark.parametrize(
    "resource_name", ["journals", "funders", "members", "licenses"]
)
async def test_non_works_count_omits_cursor(httpx_mock, client, resource_name):
    httpx_mock.add_response(
        json={"status": "ok", "message": {"items": [], "total-results": 42}}
    )
    resource = getattr(client, resource_name)
    assert await resource.count() == 42
    params = httpx_mock.get_requests()[0].url.params
    assert params["rows"] == "0"
    assert params["offset"] == "0"
    assert "cursor" not in params


async def test_non_works_iterate_uses_offset_paging_without_cursor(httpx_mock, client):
    httpx_mock.add_response(json=fixture("license_list.json"))
    httpx_mock.add_response(
        json={"status": "ok", "message": {"items": [], "total-results": 2}}
    )
    items = [item async for item in client.licenses.iterate(page_size=2)]
    assert len(items) == 2
    requests = httpx_mock.get_requests()
    assert len(requests) == 2
    assert requests[0].url.params["offset"] == "0"
    assert requests[1].url.params["offset"] == "2"
    assert all("cursor" not in r.url.params for r in requests)


async def test_types_count_and_iterate_use_single_unpaged_fetch(httpx_mock, client):
    httpx_mock.add_response(json=fixture("type_list.json"))
    httpx_mock.add_response(json=fixture("type_list.json"))
    checkpoints: list[tuple[int, str | None]] = []

    assert await client.types.count() == 30
    items = [
        item
        async for item in client.types.iterate(
            limit=1, on_page=lambda page, cursor: checkpoints.append((page, cursor))
        )
    ]
    assert [item.id for item in items] == ["book-section"]
    assert checkpoints == [(1, None)]
    for request in httpx_mock.get_requests():
        assert "cursor" not in request.url.params
        assert "rows" not in request.url.params
        assert "offset" not in request.url.params


async def test_types_iterate_limit_zero_sends_no_requests(httpx_mock, client):
    items = [item async for item in client.types.iterate(limit=0)]
    assert items == []
    assert httpx_mock.get_requests() == []


async def test_page_exposes_total_and_meta(httpx_mock, client):
    httpx_mock.add_response(json=fixture("cursor_p1.json"))
    page = await client.works.search(query="climate", cursor="*")
    assert page.total == 641402
    assert page.next_cursor == fixture_page2_cursor()
    assert page.results[0].doi == "10.1007/s002679900045"


@pytest.mark.parametrize("bad", [{"title": 5}, {"author": "not-a-list-of-objects"}])
async def test_validated_parsing_reports_the_model_name(httpx_mock, client, bad):
    body = works_envelope([{"DOI": "10.1/x", "title": ["ok"], **bad}])
    httpx_mock.add_response(json=body)
    with pytest.raises(ValidationError) as exc_info:
        await client.works.search()
    assert exc_info.value.model_name == "Work"
