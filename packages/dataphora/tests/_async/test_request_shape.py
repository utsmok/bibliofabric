"""Outgoing request shape: bracketed parameter names, headers, paging, filters."""

import pytest
from bibliofabric.exceptions import (
    APIError,
    ConfigurationError,
    NotFoundError,
    ValidationError,
)
from dataphora import (
    ClientPrefixFilters,
    DataphoraClient,
    DoiFilters,
    PrefixFilters,
    ProviderPrefixFilters,
    RepositoryFilters,
)

from ..conftest import (
    BASE_URL,
    cursor_envelope,
    doi_resource,
    envelope,
    load_fixture,
    plain_resource,
)

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


async def test_activities_read_every_page_and_number_the_pages(client, httpx_mock):
    """The next link of this route points at the global ``/activities`` route."""
    first = {
        "data": [plain_resource("a", "activities", action="update", version=2)],
        "meta": {"total": 2, "totalPages": 2, "page": 1},
        "links": {"next": f"{BASE_URL}/activities?page%5Bnumber%5D=2"},
    }
    second = {
        "data": [plain_resource("b", "activities", action="create", version=1)],
        "meta": {"total": 2, "totalPages": 2, "page": 2},
        "links": {},
    }
    httpx_mock.add_response(json=first)
    httpx_mock.add_response(json=second)
    activities = await client.dois.activities("https://doi.org/10.5438/0012")
    assert [activity.version for activity in activities] == [2, 1]
    first_request, second_request = httpx_mock.get_requests()
    assert "10.5438%2F0012/activities" in first_request.url.raw_path.decode()
    assert dict(first_request.url.params) == {"page[number]": "1", "page[size]": "1000"}
    assert second_request.url.path == "/dois/10.5438/0012/activities"
    assert dict(second_request.url.params) == {
        "page[number]": "2",
        "page[size]": "1000",
    }


async def test_empty_ids_raise_configuration_error(client):
    with pytest.raises(ConfigurationError):
        await client.dois.activities("  ")
    with pytest.raises(ConfigurationError):
        await client.clients.activities("")


async def test_base_url_override_points_elsewhere(httpx_mock, settings):
    httpx_mock.add_response(json=DOI)
    async with DataphoraClient(
        settings=settings, base_url="https://api.test.datacite.org"
    ) as test_client:
        await test_client.dois.get("10.5438/0012")
    assert last_request(httpx_mock).url.path == "/dois/10.5438/0012"
    assert str(last_request(httpx_mock).url).startswith("https://api.test.datacite.org")


async def test_batch_get_is_disabled(client):
    """No DataCite route reads several records by id."""
    with pytest.raises(ConfigurationError):
        await client.dois.batch_get(["10.5438/0012"])


@pytest.mark.parametrize("page", [0, -1, 401])
async def test_unreachable_numbered_pages_raise_configuration_error(client, page):
    """Upstream reads page 0 as page 1 and repeats the last page past 10,000."""
    with pytest.raises(ConfigurationError):
        await client.dois.search(page=page)


async def test_last_reachable_numbered_pages_are_allowed(client, httpx_mock):
    httpx_mock.add_response(json=PAGE)
    httpx_mock.add_response(json=PAGE)
    await client.dois.search(page=400)
    await client.dois.search(page=10, page_size=1000)
    assert [
        request.url.params["page[number]"] for request in httpx_mock.get_requests()
    ] == [
        "400",
        "10",
    ]


async def test_totals_send_their_parameters(client, httpx_mock):
    entry = [{"id": "cern", "count": 1}]
    httpx_mock.add_response(json=entry)
    httpx_mock.add_response(json=entry)
    httpx_mock.add_response(json=entry)
    await client.clients.totals(provider_id=["cern", "dryad"], state="findable")
    await client.providers.totals(state="consortium")
    await client.prefixes.totals("cern.zenodo")
    clients_request, providers_request, prefixes_request = httpx_mock.get_requests()
    assert clients_request.url.path == "/clients/totals"
    assert dict(clients_request.url.params) == {
        "provider-id": "cern,dryad",
        "state": "findable",
    }
    assert providers_request.url.path == "/providers/totals"
    assert dict(providers_request.url.params) == {"state": "consortium"}
    assert prefixes_request.url.path == "/prefixes/totals"
    assert dict(prefixes_request.url.params) == {"client-id": "cern.zenodo"}


async def test_totals_reject_a_body_that_is_not_an_array(client, httpx_mock):
    body = {"data": [{"id": "cern", "count": 1}]}
    httpx_mock.add_response(json=body)
    with pytest.raises(ValidationError) as info:
        await client.providers.totals()
    assert info.value.model_name == "DataphoraTotals"
    assert info.value.raw == body


async def test_account_activities_stay_on_the_account_route(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("client_activities.json"))
    httpx_mock.add_response(json=load_fixture("provider_activities.json"))
    client_page = await client.clients.activities(
        "datacite.datacite", page=2, page_size=2
    )
    provider_page = await client.providers.activities("datacite", page_size=2)
    client_request, provider_request = httpx_mock.get_requests()
    assert client_request.url.path == "/clients/datacite.datacite/activities"
    assert dict(client_request.url.params) == {"page[number]": "2", "page[size]": "2"}
    assert provider_request.url.path == "/providers/datacite/activities"
    assert dict(provider_request.url.params) == {"page[number]": "1", "page[size]": "2"}
    assert client_page.next_cursor is None
    assert provider_page.next_cursor is None


async def test_filter_models_serialize_to_upstream_names(client, httpx_mock):
    httpx_mock.add_response(json=PAGE)
    await client.dois.search(
        DoiFilters(
            sample_size=5,
            has_citations=1,
            random=True,
            field_of_science="natural sciences",
            enriched=True,
        )
    )
    params = last_params(httpx_mock)
    assert params["sample-size"] == "5"
    assert params["has-citations"] == "1"
    assert params["random"] == "true"
    assert params["field-of-science"] == "natural sciences"
    assert params["enriched"] == "true"


async def test_account_and_prefix_filter_models(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("client_prefixes.json"))
    await client.client_prefixes.search(
        ClientPrefixFilters(client_id="cern.zenodo", prefix_id="10.5281")
    )
    assert last_params(httpx_mock)["client-id"] == "cern.zenodo"
    assert last_params(httpx_mock)["prefix-id"] == "10.5281"
    httpx_mock.add_response(json=load_fixture("provider_prefixes.json"))
    await client.provider_prefixes.search(
        ProviderPrefixFilters(
            consortium_id="cadre", provider_id="dryad", prefix_id="10.5061"
        )
    )
    assert last_params(httpx_mock)["consortium-id"] == "cadre"
    assert last_params(httpx_mock)["provider-id"] == "dryad"
    assert last_params(httpx_mock)["prefix-id"] == "10.5061"
    httpx_mock.add_response(json=load_fixture("prefix.json"))
    await client.prefixes.search(
        PrefixFilters(state="unassigned", client_id="cern.zenodo")
    )
    assert last_params(httpx_mock)["state"] == "unassigned"
    assert last_params(httpx_mock)["client-id"] == "cern.zenodo"
    httpx_mock.add_response(json=load_fixture("repository.json"))
    await client.repositories.search(
        RepositoryFilters(consortium_id="cadre", client_type="periodical")
    )
    assert last_params(httpx_mock)["consortium-id"] == "cadre"
    assert last_params(httpx_mock)["client-type"] == "periodical"


async def test_heartbeat_reads_the_plain_text_answer(client, httpx_mock):
    url = "https://api.datacite.org/heartbeat"
    httpx_mock.add_response(
        url=url, text="OK\n", headers={"content-type": "text/plain; charset=utf-8"}
    )
    assert await client.heartbeat() is True
    httpx_mock.add_response(url=url, status_code=503)
    with pytest.raises(APIError, match="status 503"):
        await client.heartbeat()
    assert [request.url.path for request in httpx_mock.get_requests()] == [
        "/heartbeat",
        "/heartbeat",
    ]
