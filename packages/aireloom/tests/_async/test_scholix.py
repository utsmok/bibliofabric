"""Scholix routing: V3 by default, V2 for linkProvider, date-filter fail-fast."""

import pytest
from aireloom import ConfigurationError, ScholixFilters, ValidationError

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


async def test_date_filters_raise_configuration_error(httpx_mock, client):
    for bad_filter in (
        ScholixFilters(sourcePid="10.1234/x", from_date="2020-01-01"),
        ScholixFilters(targetPid="10.1234/y", to_date="2021"),
        {"sourcePid": "10.1234/x", "from": "2020-01-01"},
        {"sourcePid": "10.1234/x", "to": "2021"},
        {"sourcePid": "10.1234/x", "from_date": "2020-01-01"},
        {"sourcePid": "10.1234/x", "to_date": "2021"},
    ):
        with pytest.raises(ConfigurationError, match="from_date"):
            await client.scholix.search_links(bad_filter)
        with pytest.raises(ConfigurationError, match="from_date"):
            client.scholix.iterate_links(bad_filter)
        with pytest.raises(ConfigurationError, match="from_date"):
            await client.scholix.search_links_v2(bad_filter)
        with pytest.raises(ConfigurationError, match="from_date"):
            client.scholix.iterate_links_v2(bad_filter)
    assert httpx_mock.get_requests() == []


async def test_link_provider_routes_to_v2(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("scholix_page.json")))
    await client.scholix.search_links(
        ScholixFilters(sourcePid="10.1234/x", linkProvider="Crossref")
    )
    request = httpx_mock.get_request()
    assert request.url.path == "/v2/Links"
    assert params_of(request)["linkProvider"] == "Crossref"


async def test_dict_filters_supported_on_scholix(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("scholix_page.json")))
    await client.scholix.search_links(
        {"sourcePid": "10.1234/x", "linkProvider": "OpenCitations"}
    )
    request = httpx_mock.get_request()
    assert request.url.path == "/v2/Links"
    assert params_of(request)["linkProvider"] == "OpenCitations"


async def test_iterate_links_v2_routes_link_provider(httpx_mock, client):
    empty = {"currentPage": 1, "totalLinks": 0, "totalPages": 0, "result": []}
    httpx_mock.add_response(**json_response(load("scholix_page.json")))
    httpx_mock.add_response(**json_response(empty))
    filters = ScholixFilters(targetPid="10.1234/y", linkProvider="Crossref")
    collected = [link async for link in client.scholix.iterate_links(filters)]
    assert len(collected) == 1
    requests = httpx_mock.get_requests()
    assert requests[0].url.path == "/v2/Links"
    assert params_of(requests[1])["page"] == "1"


async def test_links_and_scholix_fail_fast_on_unsupported_core_params(
    httpx_mock, client
):
    with pytest.raises(ConfigurationError, match="query_param is None"):
        await client._links.search(query="quantum")
    with pytest.raises(ConfigurationError, match="sort_param is None"):
        await client._links.search(sort="date")
    with pytest.raises(ConfigurationError, match="select_param is None"):
        await client.scholix._v3.search(select=["Source"])
    with pytest.raises(ConfigurationError, match="cursor_param is None"):
        await client.scholix._v3.search(cursor="*")
    assert httpx_mock.get_requests() == []


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
    assert providers and providers[0].name == "Crossref"
    assert providers[0].total_relationships == 1200000


async def test_list_link_publishers_in_target_and_in_source(httpx_mock, client):
    httpx_mock.add_response(
        **json_response([{"name": "Elsevier", "totalRelationships": 99}])
    )
    httpx_mock.add_response(**json_response([]))
    publishers = await client.scholix.list_link_publishers(name="Elsevier")
    in_source = await client.scholix.list_link_publishers(in_target=False)
    reqs = httpx_mock.get_requests()
    assert reqs[0].url.path == "/v2/LinkPublisher/inTarget"
    assert params_of(reqs[0])["name"] == "Elsevier"
    assert publishers[0].name == "Elsevier"
    assert publishers[0].total_relationships == 99
    assert reqs[1].url.path == "/v2/LinkPublisher/inSource"
    assert in_source == []


async def test_list_link_providers_and_publishers_wrap_validation_error(
    httpx_mock, client
):
    httpx_mock.add_response(**json_response([{"totalRelationships": "not-an-int"}]))
    with pytest.raises(ValidationError):
        await client.scholix.list_link_providers()

    httpx_mock.add_response(**json_response([{"totalRelationships": "not-an-int"}]))
    with pytest.raises(ValidationError):
        await client.scholix.list_link_publishers()


async def test_iterate_links_v2_supports_on_error_skip(httpx_mock, client):
    bad_page = {
        "currentPage": 0,
        "totalLinks": 1,
        "totalPages": 1,
        "result": [{"LinkPublicationDate": "not-a-date"}],
    }
    httpx_mock.add_response(**json_response(bad_page))
    failures: list[tuple[dict, Exception]] = []
    collected = [
        link
        async for link in client.scholix.iterate_links_v2(
            None, on_error="skip", failures=failures
        )
    ]
    assert collected == []
    assert len(failures) == 1


async def test_kpi_returns_document(httpx_mock, client):
    httpx_mock.add_response(**json_response({"links": 1}))
    kpi = await client.scholix.get_kpi()
    assert httpx_mock.get_request().url.path == "/kpi/getKPI"
    assert '"links"' in kpi
