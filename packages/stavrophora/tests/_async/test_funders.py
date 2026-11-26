"""Funders helpers: descendant lists and the descendant-pinned works scope."""

import pytest
from bibliofabric.exceptions import ConfigurationError
from stavrophora import WorksFilters

from .conftest import fixture, works_envelope

FIXTURE_DESCENDANTS = fixture("funder_get.json")["message"]["descendants"]


async def test_descendants_returns_the_record_list(httpx_mock, client):
    httpx_mock.add_response(json=fixture("funder_get.json"))
    descendants = await client.funders.descendants("https://doi.org/10.13039/100000001")
    assert httpx_mock.get_requests()[0].url.path == "/v1/funders/10.13039/100000001"
    assert descendants == FIXTURE_DESCENDANTS


async def test_descendants_is_empty_without_a_hierarchy(httpx_mock, client):
    httpx_mock.add_response(
        json={
            "status": "ok",
            "message-type": "funder",
            "message": {"id": "100000025", "name": "Small Funder"},
        }
    )
    assert await client.funders.descendants("10.13039/100000025") == []


async def test_include_descendants_ors_ids_into_the_funder_filter(httpx_mock, client):
    httpx_mock.add_response(json=fixture("funder_get.json"))
    httpx_mock.add_response(json=works_envelope([]))
    scope = client.funders.works("10.13039/100000001", include_descendants=True)
    await scope.search(page_size=2)
    request = httpx_mock.get_requests()[1]
    ids = [
        entry.removeprefix("funder:")
        for entry in request.url.params["filter"].split(",")
    ]
    assert ids == ["10.13039/100000001", *FIXTURE_DESCENDANTS]


async def test_include_descendants_combines_with_user_filters(httpx_mock, client):
    httpx_mock.add_response(json=fixture("funder_get.json"))
    httpx_mock.add_response(json=works_envelope([]))
    scope = client.funders.works("10.13039/100000001", include_descendants=True)
    await scope.search(WorksFilters(type="journal-article"))
    params = httpx_mock.get_requests()[1].url.params
    assert params["filter"].startswith("type:journal-article,funder:")


async def test_include_descendants_rejects_a_user_funder_filter(httpx_mock, client):
    httpx_mock.add_response(json=fixture("funder_get.json"))
    scope = client.funders.works("10.13039/100000001", include_descendants=True)
    with pytest.raises(ConfigurationError, match="not both"):
        await scope.search({"funder": "10.13039/100000002"})
    assert len(httpx_mock.get_requests()) == 1


async def test_include_descendants_applies_to_count_and_iterate(httpx_mock, client):
    httpx_mock.add_response(json=fixture("funder_get.json"))
    httpx_mock.add_response(json=works_envelope([]))
    httpx_mock.add_response(json=works_envelope([]))
    scope = client.funders.works("10.13039/100000001", include_descendants=True)
    assert await scope.count() == 0
    collected = [work async for work in scope.iterate(page_size=2)]
    requests = httpx_mock.get_requests()
    assert len(requests) == 3
    for request in requests[1:]:
        assert "funder:10.13039/100000001" in request.url.params["filter"]
    assert collected == []
