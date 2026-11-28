"""Offline request-shape and parsing tests for the record routes."""

import pytest
from bibliofabric.exceptions import ConfigurationError, NotFoundError
from seriatim import SeriatimClient

from ..conftest import load_json_fixture

NATURE = load_json_fixture("record_print_nature.json")
ISSN_L = load_json_fixture("issn_l_nature.json")
NOT_FOUND = load_json_fixture("error_404.json")


def last_request(httpx_mock):
    return httpx_mock.get_requests()[-1]


async def test_get_record_parses_and_keeps_raw(client, httpx_mock):
    httpx_mock.add_response(json=NATURE)
    record = await client.records.get("0028-0836")
    assert record.issn == "0028-0836"
    assert record.raw == NATURE
    request = last_request(httpx_mock)
    assert request.url.path == "/resource/ISSN/0028-0836"
    assert request.headers["accept"] == "application/ld+json"


async def test_get_normalizes_compact_issn_in_path(client, httpx_mock):
    httpx_mock.add_response(json=NATURE)
    await client.records.get("00280836")
    assert last_request(httpx_mock).url.path == "/resource/ISSN/0028-0836"


async def test_invalid_issn_raises_without_request(client, httpx_mock):
    with pytest.raises(ConfigurationError, match="valid ISSN"):
        await client.records.get("9999-9999")
    with pytest.raises(ConfigurationError, match="valid ISSN"):
        await client.records.get("garbage")
    assert not httpx_mock.get_requests()


async def test_select_is_rejected_without_request(client, httpx_mock):
    with pytest.raises(ConfigurationError, match="field selection"):
        await client.records.get("0028-0836", select=["mainTitle"])
    assert not httpx_mock.get_requests()


async def test_get_issn_l_parses_cluster(client, httpx_mock):
    httpx_mock.add_response(json=ISSN_L)
    cluster = await client.issn_l.get("0028-0836")
    assert cluster.issn_l == "0028-0836"
    assert cluster.raw == ISSN_L
    assert last_request(httpx_mock).url.path == "/resource/ISSN-L/0028-0836"


async def test_not_found_maps_to_not_found_error(client, httpx_mock):
    httpx_mock.add_response(status_code=404, json=NOT_FOUND)
    httpx_mock.add_response(status_code=404, json=NOT_FOUND)
    with pytest.raises(NotFoundError):
        await client.records.get("9999-9994")
    with pytest.raises(NotFoundError):
        await client.issn_l.get("9999-9994")


async def test_exists_uses_get(client, httpx_mock):
    httpx_mock.add_response(json=NATURE)
    httpx_mock.add_response(status_code=404, json=NOT_FOUND)
    assert await client.records.exists("0028-0836") is True
    assert await client.records.exists("9999-9994") is False


async def test_raw_returns_the_node_dict(client, httpx_mock):
    httpx_mock.add_response(json=NATURE)
    node = await client.records.raw("0028-0836")
    assert node == NATURE


async def test_base_url_override_points_elsewhere(httpx_mock, settings):
    httpx_mock.add_response(json=NATURE)
    async with SeriatimClient(settings=settings, base_url="http://portal.test") as alt:
        await alt.records.get("0028-0836")
    assert last_request(httpx_mock).url.path == "/resource/ISSN/0028-0836"
