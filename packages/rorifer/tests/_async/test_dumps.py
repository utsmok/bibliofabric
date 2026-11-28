"""Zenodo data dumps: list, pick the newest, download."""

import pytest
from rorifer import ConfigurationError, RorDump

from ..conftest import load_fixture

ZENODO_SEARCH = load_fixture("zenodo_search.json")
FILE_URL = ZENODO_SEARCH["hits"]["hits"][0]["files"][0]["links"]["self"]


def hits_in_order(first: dict, second: dict) -> dict:
    return {"hits": {"hits": [first, second]}}


async def test_list_sends_community_search(client, httpx_mock):
    httpx_mock.add_response(json=ZENODO_SEARCH)
    dumps = await client.dumps.list(limit=2)
    request = httpx_mock.get_requests()[-1]
    assert request.url.host == "zenodo.org"
    assert request.url.path == "/api/records"
    assert dict(request.url.params) == {
        "q": "communities:ror-data",
        "sort": "mostrecent",
        "size": "2",
        "type": "dataset",
    }
    assert [dump.record_id for dump in dumps] == [24378467, 5534443]
    assert dumps[0].zip_url == FILE_URL


async def test_list_rejects_non_positive_limit(client, httpx_mock):
    with pytest.raises(ConfigurationError, match="limit must be positive"):
        await client.dumps.list(limit=0)
    assert not httpx_mock.get_requests()


async def test_latest_picks_newest_publication_date(client, httpx_mock):
    new, old = ZENODO_SEARCH["hits"]["hits"]
    httpx_mock.add_response(json=hits_in_order(old, new))
    assert (await client.dumps.latest()).record_id == new["id"]
    assert httpx_mock.get_requests()[-1].url.params["size"] == "25"


async def test_latest_without_records_raises(client, httpx_mock):
    httpx_mock.add_response(json={"hits": {"hits": []}})
    with pytest.raises(ConfigurationError, match="no records"):
        await client.dumps.latest()


async def test_download_streams_zip_to_disk(client, httpx_mock, tmp_path):
    payload = b"PK\x03\x04" + bytes(range(256)) * 64
    httpx_mock.add_response(url=FILE_URL, content=payload)
    dump = RorDump.model_validate(ZENODO_SEARCH["hits"]["hits"][0])

    target = await client.dumps.download(dump, tmp_path / "nested" / "ror-data.zip")

    assert target == tmp_path / "nested" / "ror-data.zip"
    assert target.read_bytes() == payload
    assert httpx_mock.get_requests()[-1].url.path.endswith("/content")


async def test_download_without_zip_raises(client, httpx_mock, tmp_path):
    dump = RorDump.model_validate({"id": 1, "files": [{"key": "a.csv"}]})
    with pytest.raises(ConfigurationError, match="no downloadable zip"):
        await client.dumps.download(dump, tmp_path / "ror.zip")
    assert not httpx_mock.get_requests()
