"""Request shape and response parsing for the per-article routes (mocked)."""

import json

import pytest
from bibliofabric.exceptions import ConfigurationError, NotFoundError

from ..conftest import (
    FIXTURES,
    citation_record,
    list_envelope,
    lite_record,
    load_fixture,
)


async def test_get_article_by_combined_id(httpx_mock, client):
    httpx_mock.add_response(json=lite_record())

    article = await client.articles.get("MED:23903748")

    request = httpx_mock.get_requests()[0]
    assert request.url.path == "/europepmc/webservices/rest/article/MED/23903748"
    assert request.url.params["format"] == "json"
    assert request.url.params["resultType"] == "core"
    assert article.id == "23903748"


async def test_get_article_rejects_bare_ids(client):
    with pytest.raises(ConfigurationError):
        await client.articles.get("23903748")


async def test_exists_is_false_on_404(httpx_mock, client):
    httpx_mock.add_response(status_code=404, json={"error": "not found"})
    assert await client.articles.exists("MED:99999999") is False


async def test_references_page_with_page_and_page_size(httpx_mock, client):
    httpx_mock.add_response(
        json=list_envelope([citation_record()], hit_count=22, page=2, page_size=2)
    )

    page = await client.articles.references("MED:23903748", page=2, page_size=2)

    request = httpx_mock.get_requests()[0]
    assert request.url.path == "/europepmc/webservices/rest/MED/23903748/references"
    assert request.url.params["page"] == "2"
    assert request.url.params["pageSize"] == "2"
    assert request.url.params["format"] == "json"
    assert page.total == 22
    assert page.page == 2
    assert page.results[0].id == "21574616"


async def test_citations_parse_the_citation_wrapper(httpx_mock, client):
    httpx_mock.add_response(
        json=list_envelope(
            [citation_record(record_id="42955633")],
            wrapper="citationList",
            item="citation",
        )
    )
    page = await client.articles.citations("MED:23903748")
    assert page.results[0].id == "42955633"


async def test_database_links_parse_the_link_wrapper(httpx_mock, client):
    httpx_mock.add_response(
        json=list_envelope(
            [{"accessionId": "Q9Y6K9", "database": "UniProt"}],
            wrapper="databaseLinkList",
            item="databaseLink",
            hit_count=1,
        )
    )
    page = await client.articles.database_links("MED:23903748", page=1, page_size=25)
    assert page.results[0].database == "UniProt"


async def test_data_links_returns_the_envelope(httpx_mock, client):
    httpx_mock.add_response(json=load_fixture("data_links.json"))

    response = await client.articles.data_links("MED:23903748")

    request = httpx_mock.get_requests()[0]
    assert request.url.path == "/europepmc/webservices/rest/MED/23903748/datalinks"
    categories = {
        category.name: category for category in response.data_link_list.category
    }
    assert "Altmetric" in categories
    links = [
        link
        for category in response.data_link_list.category
        for section in (category.section or [])
        for link in (section.linklist.link if section.linklist else [])
    ]
    link = links[0]
    assert link.target.title == "Nanometre-scale thermometry in a living cell"
    assert link.relationship_type.name == "IsReferencedBy"


async def test_labs_links_returns_provider_counts(httpx_mock, client):
    httpx_mock.add_response(json=load_fixture("labs_links.json"))
    response = await client.articles.labs_links("MED:23903748")
    assert response.links_count_list.provider[0].provider_name.startswith("BioStudies")


async def test_evaluations_returns_the_envelope(httpx_mock, client):
    httpx_mock.add_response(json=load_fixture("evaluations.json"))
    response = await client.articles.evaluations("MED:23903748")
    assert response.evaluation_list.evaluation == []
    request = httpx_mock.get_requests()[0]
    assert request.url.path == "/europepmc/webservices/rest/evaluations/MED/23903748"


async def test_full_text_xml_returns_text(httpx_mock, client):
    httpx_mock.add_response(
        content=load_fixture_text("fulltext_snippet.xml"),
        headers={"content-type": "application/xml"},
    )
    document = await client.articles.full_text_xml("PMC13810549")
    assert "<article" in document.xml
    request = httpx_mock.get_requests()[0]
    assert request.url.path == "/europepmc/webservices/rest/PMC13810549/fullTextXML"


async def test_book_xml_miss_answers_404(httpx_mock, client):
    httpx_mock.add_response(
        content=(
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            "<ns4:fullTextXMLBean><fullTextXML><pmId>NBK11637</pmId>"
            "<message>Article is not either Open Access article or a valid NBK/PM ID"
            "</message><isOpenAccess>N</isOpenAccess></fullTextXML>"
            "</ns4:fullTextXMLBean>"
        ),
        headers={"content-type": "application/xml"},
    )
    with pytest.raises(NotFoundError):
        await client.articles.book_xml("NBK11637")


async def test_supplementary_files_return_bytes(httpx_mock, client):
    httpx_mock.add_response(content=b"PK\x03\x04-zip-bytes")
    bundle = await client.articles.supplementary_files("PMC13810549")
    assert bundle.startswith(b"PK")


def load_fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text()


async def test_status_updates_sends_json_body(httpx_mock, client):
    httpx_mock.add_response(json=load_fixture("status_updates.json"))

    response = await client.articles.status_updates("PPR:PPR324115")

    request = httpx_mock.get_requests()[0]
    assert request.url.path == "/europepmc/webservices/rest/status-update-search"
    assert request.url.params["format"] == "json"
    assert request.headers["Content-Type"].startswith("application/json")
    body = json.loads(request.content)
    assert body == {"ids": [{"src": "PPR", "extId": "PPR324115"}]}
    metrics = response.metrics
    assert metrics is not None
    assert metrics.articles_queried == 30
    articles = response.articles_with_status_update or []
    article = articles[0]
    assert article.src == "PPR"
    assert article.ext_id == "PPR324115"
    assert article.status_updates == ["PUBLISHED_VERSION_AVAILABLE"]
    assert article.links[1].href == "nullMED/35166174"


async def test_status_updates_bare_id_needs_source(client):
    with pytest.raises(ConfigurationError):
        await client.articles.status_updates("PPR324115")
