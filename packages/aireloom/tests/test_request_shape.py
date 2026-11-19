"""Request shapes of the V4 entity endpoints: filter expression, sort,
select, paging parameters, count, facets, and group_by."""

import pytest
from aireloom import (
    AireloomClient,
    ConfigurationError,
    ProjectsFilters,
    ResearchProductsFilters,
)

from .conftest import json_response, load, make_settings, params_of


async def test_filter_expression_from_model(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("rp_page.json")))
    await client.research_products.search(
        ResearchProductsFilters(
            ids_doi="10.1234/abc",
            type="publication",
            subjects=["chemistry", "biology"],
            is_green=True,
            impact_citation_count=">100",
            oa_color="!gold",
        )
    )
    request = httpx_mock.get_request()
    assert request.url.path == "/v4/research-products"
    parts = set(params_of(request)["filter"].split(","))
    assert parts == {
        "ids.doi:10.1234/abc",
        "type:publication",
        "subjects:chemistry|biology",
        "is_green:true",
        "impact.citation_count:>100",
        "oa_color:!gold",
    }


async def test_filter_expression_from_dict(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("rp_page.json")))
    await client.research_products.search({"type": "dataset", "language": "!ger"})
    parts = set(params_of(httpx_mock.get_request())["filter"].split(","))
    assert parts == {"type:dataset", "language:!ger"}


async def test_query_sort_select_and_paging_params(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("rp_page.json")))
    await client.research_products.search(
        query="quantum dots",
        sort="citation_count:desc",
        select=["id", "mainTitle", "publicationDate"],
        page_size=50,
        page=2,
    )
    params = params_of(httpx_mock.get_request())
    assert params["search"] == "quantum dots"
    assert params["sort"] == "citation_count:desc"
    assert params["select"] == "id,mainTitle,publicationDate"
    assert params["page_size"] == "50"
    assert params["page"] == "2"


async def test_unknown_sort_field_rejected_without_request(httpx_mock, client):
    with pytest.raises(ConfigurationError, match="Invalid sort field 'title'"):
        await client.research_products.search(sort="title")
    assert len(httpx_mock.get_requests()) == 0


async def test_invalid_sort_direction_rejected(httpx_mock, client):
    with pytest.raises(ConfigurationError, match="asc or desc"):
        await client.research_products.search(sort="citation_count:up")
    assert len(httpx_mock.get_requests()) == 0


async def test_project_filter_aliases_and_status(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("projects_page.json")))
    await client.projects.search(ProjectsFilters(funder="EC", project_status="ongoing"))
    parts = set(params_of(httpx_mock.get_request())["filter"].split(","))
    assert parts == {"funder:EC", "project_status:ongoing"}


async def test_count_sends_minimal_cursor_page(httpx_mock, client):
    httpx_mock.add_response(
        **json_response({"header": {"numFound": 3927154}, "results": []})
    )
    total = await client.projects.count()
    assert total == 3927154
    params = params_of(httpx_mock.get_request())
    request = httpx_mock.get_request()
    assert request.url.path == "/v4/projects"
    assert params["page_size"] == "1"
    assert params["cursor"] == "*"


async def test_facets_sends_facet_parameter(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("facets.json")))
    counts = await client.research_products.facets("type", page_size=1)
    params = params_of(httpx_mock.get_request())
    assert params["facets"] == "type"
    assert params["page_size"] == "1"
    assert counts["type"] == {
        "publication": 241566601,
        "dataset": 112182103,
        "other": 43420301,
        "software": 1303995,
    }


async def test_group_by_sends_aggregation_parameter(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("group_by.json")))
    counts = await client.research_products.group_by("type")
    params = params_of(httpx_mock.get_request())
    assert params["group_by"] == "type"
    assert params["page_size"] == "1"
    assert counts["software"] == 1303995


async def test_mailto_attached_to_v4_requests_only(httpx_mock, settings):
    async with AireloomClient(
        settings=make_settings(mailto="team@example.org")
    ) as client:
        httpx_mock.add_response(**json_response(load("rp_page.json")))
        httpx_mock.add_response(**json_response(load("scholix_page.json")))
        await client.research_products.search()
        await client.scholix.search_links(None, page_size=5)
    graph_params = params_of(httpx_mock.get_requests()[0])
    scholix_params = params_of(httpx_mock.get_requests()[1])
    assert graph_params["mailto"] == "team@example.org"
    assert "mailto" not in scholix_params
