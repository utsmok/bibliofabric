"""Request shape and response parsing for the annotations, grants, profiles."""

import pytest
from bibliofabric.exceptions import ConfigurationError

from ..conftest import (
    ANNOTATIONS_BASE_URL,
    GRIST_BASE_URL,
    annotation_page,
    article_annotation,
    grist_envelope,
    load_fixture,
)


async def test_annotations_by_article_ids(httpx_mock, client):
    httpx_mock.add_response(json=[article_annotation()])

    records = await client.annotations.by_article_ids("MED:23903748", type="Chemicals")

    request = httpx_mock.get_requests()[0]
    assert str(request.url).startswith(ANNOTATIONS_BASE_URL)
    assert request.url.path == "/europepmc/annotations_api/annotationsByArticleIds"
    assert request.url.params["articleIds"] == "MED:23903748"
    assert request.url.params["type"] == "Chemicals"
    assert request.url.params["format"] == "JSON"
    assert records[0].annotations[0].exact == "nitrogen"
    assert records[0].annotations[0].tags[0].name == "nitrogen"


async def test_annotations_by_article_ids_join_lists(httpx_mock, client):
    httpx_mock.add_response(json=[article_annotation(), article_annotation("999")])
    await client.annotations.by_article_ids(["MED:1", "MED:2"])
    assert httpx_mock.get_requests()[0].url.params["articleIds"] == "MED:1,MED:2"


async def test_annotations_by_entity(httpx_mock, client):
    httpx_mock.add_response(json=annotation_page())

    page = await client.annotations.by_entity("aspirin", page_size=2)

    request = httpx_mock.get_requests()[0]
    assert request.url.path == "/europepmc/annotations_api/annotationsByEntity"
    assert request.url.params["entity"] == "aspirin"
    assert request.url.params["pageSize"] == "2"
    assert page.articles[0].ext_id == "23903748"
    assert page.next_cursor_mark == 265.731278071


async def test_annotations_by_provider(httpx_mock, client):
    httpx_mock.add_response(json=annotation_page())
    await client.annotations.by_provider("Europe PMC", page_size=2)
    request = httpx_mock.get_requests()[0]
    assert request.url.path == "/europepmc/annotations_api/annotationsByProvider"
    assert request.url.params["provider"] == "Europe PMC"


async def test_annotations_by_relationship(httpx_mock, client):
    httpx_mock.add_response(json=annotation_page())
    await client.annotations.by_relationship("aspirin", "heart")
    request = httpx_mock.get_requests()[0]
    assert request.url.params["firstEntity"] == "aspirin"
    assert request.url.params["secondEntity"] == "heart"


async def test_annotations_by_section(httpx_mock, client):
    httpx_mock.add_response(json=annotation_page())
    await client.annotations.by_section(type="Diseases")
    request = httpx_mock.get_requests()[0]
    assert request.url.path == (
        "/europepmc/annotations_api/annotationsBySectionAndOrType"
    )
    assert request.url.params["type"] == "Diseases"


async def test_annotations_by_section_needs_a_filter(client):
    with pytest.raises(ConfigurationError):
        await client.annotations.by_section()


async def test_annotations_exhausted_cursor_is_none(httpx_mock, client):
    httpx_mock.add_response(json=annotation_page(nextCursorMark=-1.0))
    page = await client.annotations.by_entity("aspirin")
    assert page.next_cursor_mark is None


async def test_grants_search(httpx_mock, client):
    httpx_mock.add_response(json=grist_envelope())

    response = await client.grants.search("malaria", page=2)

    request = httpx_mock.get_requests()[0]
    assert str(request.url).startswith(GRIST_BASE_URL)
    assert (
        request.url.path
        == "/europepmc/GristAPI/rest/get/query=malaria&format=json&page=2"
    )
    assert "pageSize" not in str(request.url)
    assert response.hit_count == "1739"
    record = response.record_list.record[0]
    assert record.grant.funder.name == "Wellcome Trust"


async def test_grants_iterate_stops_on_empty_page(httpx_mock, client):
    httpx_mock.add_response(json=grist_envelope())
    httpx_mock.add_response(json=grist_envelope(records=[]))
    records = await client.grants.iterate("malaria")
    assert len(records) == 1
    assert len(httpx_mock.get_requests()) == 2


async def test_profile_returns_counts(httpx_mock, client):
    httpx_mock.add_response(json=load_fixture("profile.json"))
    response = await client.profiles.profile('AUTH:"Mok S"')
    request = httpx_mock.get_requests()[0]
    assert request.url.path == "/europepmc/webservices/rest/profile"
    assert request.url.params["profiletype"] == "all"
    assert request.url.params["format"] == "json"
    assert response.profile_list.pub_type[0].name == "ALL"
