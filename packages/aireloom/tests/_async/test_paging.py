"""Iteration over cursor and page-based routes, including the cursor-echo
stop, the 100-per-page graph default, and checkpoint resumes."""

from aireloom import ResearchProductsFilters

from .conftest import json_response, load, params_of


async def test_iterate_walks_cursor_pages(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("rp_cursor_p1.json")))
    httpx_mock.add_response(**json_response(load("rp_cursor_p2.json")))
    checkpoints: list[tuple[int, str | None]] = []
    collected = [
        product
        async for product in client.research_products.iterate(
            ResearchProductsFilters(type="publication"),
            on_page=lambda number, cursor: checkpoints.append((number, cursor)),
        )
    ]
    requests = httpx_mock.get_requests()
    assert len(requests) == 2
    first = params_of(requests[0])
    assert first["page_size"] == "100"
    assert first["cursor"] == "*"
    assert first["filter"] == "type:publication"
    assert params_of(requests[1])["cursor"].startswith("AoM/")
    assert [product.id for product in collected] == [load("rp_by_id.json")["id"]] * 2
    assert checkpoints == [(1, params_of(requests[1])["cursor"]), (2, None)]


async def test_iterate_stops_when_api_echoes_cursor(httpx_mock, client):
    echoed = {
        "header": {"numFound": 3, "pageSize": 100, "nextCursor": "cur2"},
        "results": [{"id": "a::1", "type": "publication"}],
    }
    echo_back = {
        "header": {"numFound": 3, "pageSize": 100, "nextCursor": "cur2"},
        "results": [],
    }
    httpx_mock.add_response(**json_response(echoed))
    httpx_mock.add_response(**json_response(echo_back))
    checkpoints: list[tuple[int, str | None]] = []
    collected = [
        product
        async for product in client.research_products.iterate(
            page_size=100,
            on_page=lambda number, cursor: checkpoints.append((number, cursor)),
        )
    ]
    assert [product.id for product in collected] == ["a::1"]
    assert checkpoints == [(1, "cur2"), (2, None)]
    assert len(httpx_mock.get_requests()) == 2
    assert params_of(httpx_mock.get_requests()[1])["cursor"] == "cur2"


async def test_iterate_resumes_from_saved_cursor(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("rp_cursor_p2.json")))
    collected = [
        product
        async for product in client.research_products.iterate(cursor="AoM/saved")
    ]
    assert params_of(httpx_mock.get_request())["cursor"] == "AoM/saved"
    assert len(collected) == 1


async def test_iterate_stops_at_limit(httpx_mock, client):
    page = {
        "header": {"numFound": 500, "pageSize": 100},
        "results": [{"id": f"a::{n}", "type": "publication"} for n in range(100)],
    }
    httpx_mock.add_response(**json_response(page))
    collected = [product async for product in client.research_products.iterate(limit=7)]
    assert len(collected) == 7
    assert len(httpx_mock.get_requests()) == 1


async def test_links_default_page_window(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("links_page.json")))
    page = await client.research_products.search_links()
    params = params_of(httpx_mock.get_request())
    request = httpx_mock.get_request()
    assert request.url.path == "/v3/research-products/links"
    assert params["page"] == "0"
    assert params["pageSize"] == "99"
    assert page.total == 116


async def test_links_explicit_page_and_size(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("links_page.json")))
    await client.research_products.search_links(page=3, page_size=50)
    params = params_of(httpx_mock.get_request())
    assert params["page"] == "3"
    assert params["pageSize"] == "50"


async def test_links_iterate_stops_on_empty_page(httpx_mock, client):
    empty = {"header": {"page": 1, "totalPages": 12, "totalLinks": 116}, "results": []}
    httpx_mock.add_response(**json_response(load("links_page.json")))
    httpx_mock.add_response(**json_response(empty))
    collected = [
        relation async for relation in client.research_products.iterate_links()
    ]
    assert len(collected) == 1
    assert len(httpx_mock.get_requests()) == 2
    assert params_of(httpx_mock.get_requests()[1])["page"] == "1"
