"""Outgoing request shape: bracketed parameter names, headers, paging, filters."""

import pytest
from bibliofabric.exceptions import NotFoundError
from dataphora import DataphoraClient, DoiFilters

from ..conftest import cursor_envelope, doi_resource, envelope, load_fixture

DOI = load_fixture("doi.json")
PAGE = load_fixture("dois_list.json")
NOT_FOUND = load_fixture("notfound.json")
CLIENT_PAGE = load_fixture("client.json")


def last_request(httpx_mock):
    return httpx_mock.get_requests()[-1]


def last_params(httpx_mock) -> dict[str, str]:
    return dict(last_request(httpx_mock).url.params)


async def test_get_sends_the_doi_path_and_json_api_accept(client, httpx_mock):
    httpx_mock.add_response(json=DOI)
    doi = await client.dois.get("https://doi.org/10.5438/0012")
    assert doi.doi == "10.5438/0012"
    request = last_request(httpx_mock)
    assert request.url.path == "/dois/10.5438/0012"
    assert dict(request.url.params) == {}
    assert request.headers["accept"] == "application/vnd.api+json"
    assert "dataphora/" in request.headers["user-agent"]


async def test_get_raises_not_found(client, httpx_mock):
    httpx_mock.add_response(json=NOT_FOUND, status_code=404)
    with pytest.raises(NotFoundError):
        await client.dois.get("10.5438/nosuchdoi9999")


async def test_exists_uses_head(client, httpx_mock):
    httpx_mock.add_response(status_code=200)
    httpx_mock.add_response(status_code=404)
    assert await client.dois.exists("10.5438/0012") is True
    assert await client.dois.exists("10.5438/nosuchdoi9999") is False
    requests = httpx_mock.get_requests()
    assert [r.method for r in requests] == ["HEAD", "HEAD"]
    assert requests[0].url.path == "/dois/10.5438/0012"


async def test_search_sends_numbered_paging_by_default(client, httpx_mock):
    httpx_mock.add_response(json=PAGE)
    await client.dois.search()
    assert last_params(httpx_mock) == {
        "page[number]": "1",
        "page[size]": "25",
    }


async def test_search_forwards_query_sort_and_select(client, httpx_mock):
    httpx_mock.add_response(json=PAGE)
    await client.dois.search(
        DoiFilters(prefix="10.5438"),
        query="metadata schema",
        sort="-updated",
        select=["doi", "titles"],
    )
    params = last_params(httpx_mock)
    assert params == {
        "prefix": "10.5438",
        "query": "metadata schema",
        "sort": "-updated",
        "fields[dois]": "doi,titles",
        "page[number]": "1",
        "page[size]": "25",
    }


async def test_search_accepts_mapping_filters_with_dashes(client, httpx_mock):
    httpx_mock.add_response(json=PAGE)
    await client.dois.search(
        {"client-id": "cern.zenodo", "resource-type-id": "dataset"}
    )
    params = last_params(httpx_mock)
    assert params["client-id"] == "cern.zenodo"
    assert params["resource-type-id"] == "dataset"


async def test_search_forwards_extra_params(client, httpx_mock):
    httpx_mock.add_response(json=PAGE)
    await client.dois.search(params={"detail": "true", "affiliation": "true"})
    params = last_params(httpx_mock)
    assert params["detail"] == "true"
    assert params["affiliation"] == "true"


async def test_page_size_above_1000_is_clamped(client, httpx_mock):
    httpx_mock.add_response(json=PAGE)
    await client.dois.search(page_size=1001)
    assert last_params(httpx_mock)["page[size]"] == "1000"


async def test_count_requests_one_record(client, httpx_mock):
    httpx_mock.add_response(json=envelope([doi_resource()]))
    total = await client.dois.count({"prefix": "10.5438"})
    assert total == 1
    assert last_params(httpx_mock) == {
        "page[number]": "1",
        "page[size]": "1",
        "prefix": "10.5438",
    }


async def test_iterate_walks_cursor_pages(client, httpx_mock):
    first_page = cursor_envelope(
        [doi_resource(f"10.5438/{index:04d}") for index in range(1000)],
        total=1001,
        next_cursor="QUJDRA",
    )
    second_page = cursor_envelope(
        [doi_resource("10.5438/9999")], total=1001, next_cursor=None
    )
    httpx_mock.add_response(json=first_page)
    httpx_mock.add_response(json=second_page)
    records = [record async for record in client.dois.iterate()]
    assert len(records) == 1001
    first, second = httpx_mock.get_requests()
    assert dict(first.url.params) == {
        "page[cursor]": "1",
        "page[size]": "1000",
    }
    assert second.url.params["page[cursor]"] == "QUJDRA"
    assert second.url.params["page[size]"] == "1000"


async def test_iterate_respects_limit(client, httpx_mock):
    page = cursor_envelope(
        [doi_resource(f"10.5438/{index:04d}") for index in range(5)],
        total=100,
        next_cursor="QUJDRA",
    )
    httpx_mock.add_response(json=page)
    records = [record async for record in client.dois.iterate(limit=2)]
    assert len(records) == 2
    assert len(httpx_mock.get_requests()) == 1


async def test_each_resource_names_its_own_field_selection(client, httpx_mock):
    httpx_mock.add_response(json=CLIENT_PAGE)
    await client.clients.search(select=["name", "symbol"])
    params = last_params(httpx_mock)
    assert params["fields[clients]"] == "name,symbol"
    assert last_request(httpx_mock).url.path == "/clients"


async def test_client_dois_filter_the_doi_route(client, httpx_mock):
    httpx_mock.add_response(json=PAGE)
    page = await client.clients.dois("cern.zenodo", page_size=10)
    assert page.results[0].doi == PAGE["data"][0]["attributes"]["doi"]
    params = last_params(httpx_mock)
    assert params["client-id"] == "cern.zenodo"
    assert params["page[size]"] == "10"
    assert last_request(httpx_mock).url.path == "/dois"


async def test_provider_dois_filter_the_doi_route(client, httpx_mock):
    httpx_mock.add_response(json=PAGE)
    await client.providers.dois("datacite")
    assert last_params(httpx_mock)["provider-id"] == "datacite"


async def test_prefix_dois_filter_the_doi_route(client, httpx_mock):
    httpx_mock.add_response(json=PAGE)
    await client.prefixes.dois("10.5438")
    assert last_params(httpx_mock)["prefix"] == "10.5438"


async def test_repository_dois_filter_the_doi_route(client, httpx_mock):
    httpx_mock.add_response(json=PAGE)
    await client.repositories.dois("datacite.datacite")
    assert last_params(httpx_mock)["client-id"] == "datacite.datacite"


async def test_activities_request_shape_and_parsing(client, httpx_mock):
    payload = load_fixture("doi_activities.json")
    httpx_mock.add_response(json=payload)
    activities = await client.dois.activities("https://doi.org/10.5438/0012")
    assert last_request(httpx_mock).url.path == "/dois/10.5438/0012/activities"
    assert activities[0].action == "update"
    assert activities[0].version == 81


async def test_base_url_override_points_elsewhere(httpx_mock, settings):
    httpx_mock.add_response(json=DOI)
    async with DataphoraClient(
        settings=settings, base_url="https://api.test.datacite.org"
    ) as test_client:
        await test_client.dois.get("10.5438/0012")
    assert last_request(httpx_mock).url.path == "/dois/10.5438/0012"
    assert str(last_request(httpx_mock).url).startswith("https://api.test.datacite.org")
