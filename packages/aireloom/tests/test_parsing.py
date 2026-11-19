"""Parsing of trimmed real payloads into the typed models."""

from .conftest import json_response, load


async def test_search_parses_research_product(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("rp_page.json")))
    page = await client.research_products.search()
    record = load("rp_by_id.json")
    assert page.total == 241566601
    product = page.results[0]
    assert product.id == record["id"]
    assert product.type == "publication"
    assert product.mainTitle == record["mainTitle"]
    assert product.publicationDate == "2026-01-16"
    assert product.language.label == "French"


async def test_get_by_id_parses_bare_record(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("rp_by_id.json")))
    product = await client.research_products.get(
        "doi_dedup___::016e036dfe4204781ee9bf94c8b06c1b"
    )
    request = httpx_mock.get_request()
    assert request.url.path == (
        "/v3/research-products/doi_dedup___::016e036dfe4204781ee9bf94c8b06c1b"
    )
    assert product.id == load("rp_by_id.json")["id"]
    assert product.type == "publication"


async def test_persons_parse(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("persons_page.json")))
    page = await client.persons.search()
    person = page.results[0]
    assert person.id.startswith("orcid_______::")
    assert person.givenName == "Paolo"
    assert person.pid[0].typeCode == "orcid"


async def test_projects_parse(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("projects_page.json")))
    page = await client.projects.search()
    project = page.results[0]
    assert project.id
    assert project.code or project.acronym


async def test_organizations_and_data_sources_parse(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("organizations_page.json")))
    httpx_mock.add_response(**json_response(load("data_sources_page.json")))
    orgs = await client.organizations.search()
    sources = await client.data_sources.search()
    assert orgs.results[0].id
    assert sources.results[0].id


async def test_invalid_record_skipped_and_reported(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("rp_invalid_type.json")))
    failures: list[tuple[dict, Exception]] = []
    collected = await client.research_products.collect(
        on_error="skip", failures=failures
    )
    assert collected == []
    assert len(failures) == 1
    assert failures[0][0]["id"] == "bad::1"


async def test_links_parse_relations(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("links_page.json")))
    page = await client.research_products.search_links()
    relation = page.results[0]
    assert relation.relType is not None
    assert relation.source is not None and relation.target is not None


async def test_relations_info_parses(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("relations_info.json")))
    info = await client.research_products.get_relations_info()
    assert info[0].relation == "Cites"
    assert info[0].inverse == "IsCitedBy"
