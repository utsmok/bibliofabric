"""Scholix routing: V3 by default, V2 for date filters, plus V2 helpers."""

from aireloom import ScholixFilters

from .conftest import json_response, load, params_of


async def test_search_defaults_to_v3(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("scholix_page.json")))
    page = await client.scholix.search_links(None, page_size=25)
    request = httpx_mock.get_request()
    assert request.url.host == "scholix.test"
    assert request.url.path == "/v3/Links"
    params = params_of(request)
    assert params["page"] == "0"
    assert params["size"] == "25"
    assert page.total == 116
    assert page.results[0].relationship_type.name == "IsRelatedTo"


async def test_date_filters_route_to_v2(httpx_mock, client):

    httpx_mock.add_response(**json_response(load("scholix_page.json")))
    await client.scholix.search_links(
        ScholixFilters(sourcePid="10.1234/x", from_date="2020-01-01")
    )
    request = httpx_mock.get_request()
    assert request.url.path == "/v2/Links"
    params = params_of(request)
    assert params["sourcePid"] == "10.1234/x"
    assert params["from"] == "2020-01-01"
    assert "to" not in params


async def test_iterate_links_routes_dates_to_v2(httpx_mock, client):

    empty = {"currentPage": 1, "totalLinks": 0, "totalPages": 0, "result": []}
    httpx_mock.add_response(**json_response(load("scholix_page.json")))
    httpx_mock.add_response(**json_response(empty))
    filters = ScholixFilters(targetPid="10.1234/y", to_date="2021")
    collected = [link async for link in client.scholix.iterate_links(filters)]
    assert len(collected) == 1
    requests = httpx_mock.get_requests()
    assert requests[0].url.path == "/v2/Links"
    assert params_of(requests[1])["page"] == "1"


async def test_explicit_v2_endpoint(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("scholix_page.json")))
    await client.scholix.search_links_v2(None, page=1, page_size=10)
    params = params_of(httpx_mock.get_request())
    assert httpx_mock.get_request().url.path == "/v2/Links"
    assert params["page"] == "1"
    assert params["size"] == "10"


async def test_list_link_providers(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("scholix_providers.json")))
    providers = await client.scholix.list_link_providers()
    request = httpx_mock.get_request()
    assert request.url.path == "/v2/LinkProvider"
    assert providers and providers[0].name


async def test_list_link_publishers_in_target(httpx_mock, client):
    httpx_mock.add_response(**json_response([]))
    publishers = await client.scholix.list_link_publishers(name="Elsevier")
    request = httpx_mock.get_request()
    assert request.url.path == "/v2/LinkPublisher/inTarget"
    assert params_of(request)["name"] == "Elsevier"
    assert publishers == []


async def test_kpi_returns_document(httpx_mock, client):
    httpx_mock.add_response(**json_response({"links": 1}))
    kpi = await client.scholix.get_kpi()
    assert httpx_mock.get_request().url.path == "/kpi/getKPI"
    assert '"links"' in kpi
