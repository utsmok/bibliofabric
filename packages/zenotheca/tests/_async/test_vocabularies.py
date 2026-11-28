"""Outgoing request shape and parsing for the vocabularies client."""

import pytest
from zenotheca import ConfigurationError, NotFoundError

from ..conftest import (
    VOCAB_NAME,
    load_fixture,
    vocab_entry,
    vocab_envelope,
)

NOT_FOUND = load_fixture("notfound.json")


async def test_search_builds_vocabulary_path_and_params(client, httpx_mock):
    httpx_mock.add_response(json=vocab_envelope([vocab_entry()], total=43))
    page = await client.vocabularies.search(
        VOCAB_NAME, query="publication", page=2, page_size=10
    )
    request = httpx_mock.get_requests()[-1]
    assert request.url.path == f"/api/vocabularies/{VOCAB_NAME}"
    assert request.url.params["q"] == "publication"
    assert request.url.params["page"] == "2"
    assert request.url.params["size"] == "10"
    assert page.results[0].id == "publication"
    assert page.results[0].english_title == "Publication"
    assert page.total == 43


async def test_iterate_follows_pages_until_total(client, httpx_mock):
    httpx_mock.add_response(json=vocab_envelope([vocab_entry("publication")], total=2))
    httpx_mock.add_response(json=vocab_envelope([vocab_entry("dataset")], total=2))
    entries = [
        entry async for entry in client.vocabularies.iterate(VOCAB_NAME, page_size=1)
    ]
    assert [entry.id for entry in entries] == ["publication", "dataset"]


async def test_iterate_respects_limit(client, httpx_mock):
    httpx_mock.add_response(json=vocab_envelope([vocab_entry()], total=99))
    entries = [
        entry async for entry in client.vocabularies.iterate(VOCAB_NAME, limit=1)
    ]
    assert len(entries) == 1


async def test_get_returns_validated_entry(client, httpx_mock):
    httpx_mock.add_response(json=vocab_entry("dataset"))
    entry = await client.vocabularies.get(VOCAB_NAME, "dataset")
    request = httpx_mock.get_requests()[-1]
    assert request.url.path == f"/api/vocabularies/{VOCAB_NAME}/dataset"
    assert entry.revision_id == 1


async def test_get_unknown_name_is_not_found(client, httpx_mock):
    httpx_mock.add_response(status_code=404, json=NOT_FOUND)
    with pytest.raises(NotFoundError):
        await client.vocabularies.get("datatypes", "publication")


async def test_bad_vocabulary_name_raises_without_request(client, httpx_mock):
    with pytest.raises(ConfigurationError):
        async for _ in client.vocabularies.iterate("bad/name"):
            pass
    assert httpx_mock.get_requests() == []


async def test_subcommunities_requests_the_sub_route(client, httpx_mock):
    httpx_mock.add_response(json=vocab_envelope([], total=0))
    page = await client.communities.subcommunities("zenodo")
    request = httpx_mock.get_requests()[-1]
    assert request.url.path == "/api/communities/zenodo/subcommunities"
    assert page.total == 0
    assert page.results == []


async def test_invalid_subcommunity_input(client, httpx_mock):
    with pytest.raises(ConfigurationError):
        await client.communities.subcommunities("")
    assert httpx_mock.get_requests() == []
