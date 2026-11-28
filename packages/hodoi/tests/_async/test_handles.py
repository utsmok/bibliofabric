"""Handle records, landing URLs, and the ``/api/handles/`` parameters."""

import pytest
from hodoi import ConfigurationError, NotFoundError

from ..conftest import load_fixture

HANDLE = load_fixture("handle_crossref.json")


def last_request(httpx_mock):
    return httpx_mock.get_requests()[-1]


async def test_handle_reads_record(client, httpx_mock):
    httpx_mock.add_response(json=HANDLE)
    record = await client.handle("10.1038/nature12373")
    assert record.responseCode == 1
    assert record.handle == "10.1038/nature12373"
    types = [value.type for value in record.values]
    assert types == ["URL", "700050", "HS_ADMIN"]
    assert last_request(httpx_mock).url.path == "/api/handles/10.1038/nature12373"
    assert not dict(last_request(httpx_mock).url.params)


async def test_handle_parses_url_and_admin_values(client, httpx_mock):
    httpx_mock.add_response(json=HANDLE)
    record = await client.handle("10.1038/nature12373")
    url_entry = record.values[0]
    assert url_entry.index == 1
    assert url_entry.ttl == 86400
    assert url_entry.timestamp == "2023-05-18T18:13:47Z"
    assert url_entry.data.format == "string"
    assert url_entry.data.value == "https://www.nature.com/articles/nature12373"
    admin = record.values[2]
    assert admin.data.format == "admin"
    assert admin.data.value is not None
    assert admin.data.value.handle == "0.na/10.1038"
    assert admin.data.value.index == 200


async def test_handle_sends_filters_and_auth(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("handle_type_url.json"))
    await client.handle("10.1038/nature12373", index=1, type="URL", auth=True)
    assert dict(last_request(httpx_mock).url.params) == {
        "index": "1",
        "type": "URL",
        "auth": "true",
    }


async def test_handle_unknown_doi_raises_not_found(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("handle_unknown.json"), status_code=404)
    with pytest.raises(NotFoundError):
        await client.handle("10.9999/nope")


async def test_landing_url_reads_url_entry_without_fetching(client, httpx_mock):
    httpx_mock.add_response(json=HANDLE)
    url = await client.landing_url("https://doi.org/10.1038/nature12373")
    assert url == "https://www.nature.com/articles/nature12373"
    assert len(httpx_mock.get_requests()) == 1


async def test_landing_url_raises_without_url_entry(client, httpx_mock):
    httpx_mock.add_response(
        json={
            "responseCode": 1,
            "handle": "10.1/abc",
            "values": [
                {
                    "index": 100,
                    "type": "HS_ADMIN",
                    "data": {
                        "format": "admin",
                        "value": {"handle": "0.na/10.1234", "index": 200},
                    },
                }
            ],
        }
    )
    with pytest.raises(ConfigurationError, match="no URL value"):
        await client.landing_url("10.1234/abc")
