"""Parsing of trimmed real payloads into the typed models."""

import pytest
from aireloom import (
    DataSource,
    Organization,
    Person,
    Project,
    ResearchProduct,
    ValidationError,
)
from aireloom.models import Category, RelatedInstance
from aireloom.unwrapper import OpenAireUnwrapper, ScholixUnwrapper

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


async def test_relations_info_raises_validation_error(httpx_mock, client):
    httpx_mock.add_response(**json_response([{"relation": ["bad-type"]}]))
    with pytest.raises(ValidationError):
        await client.research_products.get_relations_info()


def test_project_keywords_splitting_and_original_ids():
    p_semi = Project.model_validate(
        {
            "id": "p::1",
            "keywords": "machine learning; neural networks; climate",
            "originalIds": ["corda::1"],
            "startDate": "2022-03-01",
            "endDate": "2025-12-31",
            "fundings": [{"shortName": "EC", "jurisdiction": "EU"}],
        }
    )
    assert p_semi.keywords == ["machine learning", "neural networks", "climate"]
    assert p_semi.originalIds == ["corda::1"]
    assert p_semi.funder_name == "EC"
    assert p_semi.funder_jurisdiction == "EU"
    assert p_semi.start_year == 2022
    assert p_semi.end_year == 2025

    p_comma = Project.model_validate({"id": "p::2", "keywords": "alpha, beta"})
    assert p_comma.keywords == ["alpha", "beta"]

    p_single = Project.model_validate({"id": "p::3", "keywords": "single"})
    assert p_single.keywords == ["single"]

    p_empty = Project.model_validate({"id": "p::4", "keywords": "   "})
    assert p_empty.keywords == []


def test_organization_links_and_computed_fields():
    org = Organization.model_validate(
        {
            "id": "org::1",
            "legalName": "University of Twente",
            "country": {"code": "NL", "label": "Netherlands"},
            "pids": [{"scheme": "ROR", "value": "https://ror.org/006hf6230"}],
            "links": [
                {
                    "header": {
                        "relationType": "projectOrganization",
                        "relatedIdentifier": "p::1",
                    },
                    "projectTitle": "Test Project",
                }
            ],
        }
    )
    assert org.ror_id == "https://ror.org/006hf6230"
    assert org.country_code == "NL"
    assert len(org.links) == 1
    assert org.links[0].projectTitle == "Test Project"


def test_person_context_category_and_orcid_from_pid():
    person = Person.model_validate(
        {
            "id": "person::1",
            "givenName": "Ada",
            "familyName": "Lovelace",
            "pid": [{"value": "0000-0002-1825-0097", "typeCode": "orcid"}],
            "context": [
                {
                    "id": "ctx::1",
                    "label": "Community",
                    "category": [
                        {
                            "id": "cat::1",
                            "label": "Computing",
                            "concept": [{"id": "con::1", "label": "Algorithms"}],
                        },
                        "legacy-string-category",
                    ],
                }
            ],
        }
    )
    assert person.orcid == "0000-0002-1825-0097"
    assert person.full_name == "Ada Lovelace"
    cat = person.context[0].category[0]
    assert isinstance(cat, Category)
    assert cat.concept[0].label == "Algorithms"
    assert person.context[0].category[1] == "legacy-string-category"


def test_research_product_geolocation_related_instances_and_computed_fields():
    rp = ResearchProduct.model_validate(
        {
            "id": "rp::1",
            "type": "publication",
            "mainTitle": "Test Paper",
            "publicationDate": "2024-06-01",
            "pids": [
                {"scheme": "doi", "value": "10.1234/one"},
                {"scheme": "DOI", "value": "10.1234/two"},
            ],
            "bestAccessRight": {"code": "c_abf2", "label": "OPEN"},
            "container": {"name": "Nature"},
            "authors": [{"fullName": "Doe, Jane"}],
            "indicators": {"citationImpact": {"citationCount": 42}},
            "instances": [
                {
                    "accessRight": {"label": "OPEN"},
                    "urls": ["https://example.org/pdf"],
                    "license": "CC-BY-4.0",
                }
            ],
            "geoLocations": [{"point": "52.22,6.89", "place": "Enschede"}],
            "links": [
                {
                    "header": {"relatedIdentifier": "rp::2"},
                    "instances": [
                        {
                            "instancetype": "Article",
                            "url": ["https://example.org/lower"],
                            "hostedby": {"dsId": "ds::1", "dsName": "Repo"},
                            "dateofacceptance": "2023-05-01",
                        },
                        {
                            "type": "Dataset",
                            "urls": ["https://example.org/camel"],
                            "publicationDate": "2024-01-01",
                        },
                    ],
                }
            ],
        }
    )
    assert rp.doi == "10.1234/one"
    assert rp.all_dois == ["10.1234/one", "10.1234/two"]
    assert rp.is_open_access is True
    assert rp.open_access_url == "https://example.org/pdf"
    assert rp.citation_count == 42
    assert rp.publication_year == 2024
    assert rp.journal_name == "Nature"
    assert rp.author_names == ["Doe, Jane"]
    assert rp.license == "CC-BY-4.0"
    assert rp.geoLocations[0].point == "52.22,6.89"
    inst_lower = rp.links[0].instances[0]
    inst_camel = rp.links[0].instances[1]
    assert isinstance(inst_lower, RelatedInstance)
    assert inst_lower.instancetype == "Article"
    assert inst_lower.url == ["https://example.org/lower"]
    assert inst_lower.hostedby.dsName == "Repo"
    assert inst_lower.dateofacceptance == "2023-05-01"
    assert inst_camel.instancetype == "Dataset"
    assert inst_camel.url == ["https://example.org/camel"]
    assert inst_camel.dateofacceptance == "2024-01-01"


def test_data_source_repr_and_type_name():
    ds_empty = DataSource.model_validate({"id": "ds::1"})
    assert ds_empty.type_name is None
    assert repr(ds_empty) == "DataSource(id='ds::1')"

    ds_typed = DataSource.model_validate(
        {"id": "ds::2", "type": {"scheme": "dnet", "value": "Repository"}}
    )
    assert ds_typed.type_name == "Repository"
    assert repr(ds_typed) == "DataSource(id='ds::2', type='Repository')"


def test_unwrapper_edge_cases():
    oa = OpenAireUnwrapper()
    assert oa.total({"header": {"numFound": None, "totalLinks": 42}}) == 42
    with pytest.raises(ValueError, match="no results"):
        oa.item({"results": []})

    sx = ScholixUnwrapper()
    with pytest.raises(ValueError, match="no results"):
        sx.item({"result": []})
