"""Outgoing request shape and row handling of the Meta API client."""

import pytest
from bibliofabric.exceptions import ConfigurationError

from ..conftest import load_fixture, load_fixture_json, metadata_row


def last_request(httpx_mock):
    return httpx_mock.get_requests()[-1]


async def test_metadata_request_and_row(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture_json("metadata.json"))
    rows = await client.meta.metadata("doi:10.1007/978-1-4020-9632-7")
    request = last_request(httpx_mock)
    assert request.url.path == "/meta/v1/metadata/doi:10.1007/978-1-4020-9632-7"
    assert request.headers["accept"] == "application/json"
    assert rows[0].publisher.startswith("Springer Science")
    assert rows[0].identifiers[1].scheme == "isbn"


async def test_metadata_packs_several_ids_with_double_underscore(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture_json("metadata_multi.json"))
    ids = ["doi:10.1108/jd-12-2013-0166", "doi:10.1016/j.websem.2012.08.001"]
    rows = await client.meta.metadata(ids)
    assert (
        last_request(httpx_mock).url.path
        == "/meta/v1/metadata/doi:10.1108/jd-12-2013-0166__doi:10.1016/j.websem.2012.08.001"
    )
    assert len(rows) == 2
    assert rows[1].title.startswith("Setting Our Bibliographic")


async def test_metadata_accepts_a_packed_string(client, httpx_mock):
    httpx_mock.add_response(json=[])
    await client.meta.metadata("doi:a__omid:br/1")
    assert last_request(httpx_mock).url.path == "/meta/v1/metadata/doi:a__omid:br/1"


async def test_metadata_unknown_id_answers_empty_list(client, httpx_mock):
    httpx_mock.add_response(json=[])
    assert await client.meta.metadata("doi:10.9999/nonexistent.000") == []


async def test_metadata_rejects_unknown_scheme(client):
    with pytest.raises(ConfigurationError, match="unsupported scheme"):
        await client.meta.metadata("handle:1234")


async def test_author_and_editor_person_ids(client, httpx_mock):
    httpx_mock.add_response(json=[metadata_row()])
    httpx_mock.add_response(json=load_fixture_json("editor.json"))
    authored = await client.meta.author("orcid:0000-0002-8420-0696")
    assert last_request(httpx_mock).url.params["format"] == "json"
    edited = await client.meta.editor("orcid:0000-0003-2098-4759")
    assert (
        last_request(httpx_mock).url.path == "/meta/v1/editor/orcid:0000-0003-2098-4759"
    )
    assert authored[0].authors
    assert edited[0].editors


async def test_person_id_rejects_document_schemes(client):
    with pytest.raises(ConfigurationError, match="unsupported scheme"):
        await client.meta.author("doi:10.1038/nature12373")


async def test_metadata_csv_parses_into_the_same_model(client, httpx_mock):
    httpx_mock.add_response(
        text=load_fixture("metadata.csv"),
        headers={"content-type": "text/csv; charset=utf-8"},
    )
    rows = await client.meta.metadata(
        "doi:10.1007/978-1-4020-9632-7",
        format="csv",
        sort="asc(pub_date)",
    )
    path = last_request(httpx_mock).url
    assert path.params["sort"] == "asc(pub_date)"
    assert path.params["format"] == "csv"
    assert rows[0].type == "book"
