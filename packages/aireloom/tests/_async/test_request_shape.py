"""Request shapes of the V4 entity endpoints: filter expression, sort,
select, paging parameters, count, facets, and group_by."""

from datetime import date

import pytest
from aireloom import (
    AireloomClient,
    APIError,
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


async def test_count_sends_minimal_page(httpx_mock, client):
    httpx_mock.add_response(
        **json_response({"header": {"numFound": 3927154}, "results": []})
    )
    total = await client.projects.count()
    assert total == 3927154
    params = params_of(httpx_mock.get_request())
    request = httpx_mock.get_request()
    assert request.url.path == "/v4/projects"
    assert params["page_size"] == "1"
    assert params["page"] == "1"
    assert "cursor" not in params


async def test_page_size_clamped_to_100(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("rp_page.json")))
    await client.research_products.search(page_size=500)
    assert params_of(httpx_mock.get_request())["page_size"] == "100"


async def test_offset_ceiling_and_invalid_page_rejected(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("rp_page.json")))
    await client.research_products.search(page=101, page_size=100)
    assert params_of(httpx_mock.get_request())["page"] == "101"

    with pytest.raises(ConfigurationError, match="10000"):
        await client.research_products.search(page=102, page_size=100)
    with pytest.raises(ConfigurationError, match="page must be >= 1"):
        await client.research_products.search(page=0, page_size=10)
    assert len(httpx_mock.get_requests()) == 1


async def test_empty_filter_model_and_empty_list_omitted(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("rp_page.json")))
    httpx_mock.add_response(**json_response(load("rp_page.json")))
    await client.research_products.search(ResearchProductsFilters())
    await client.research_products.search(ResearchProductsFilters(subjects=[]))
    for req in httpx_mock.get_requests():
        assert "filter" not in params_of(req)


async def test_filter_or_limit_enforced_client_side(httpx_mock, client):
    too_many = [f"10.1/{i}" for i in range(51)]
    with pytest.raises(ConfigurationError, match="at most 50"):
        await client.research_products.search(ResearchProductsFilters(ids_doi=too_many))
    with pytest.raises(ConfigurationError, match="at most 50"):
        await client.research_products.search({"ids.doi": "|".join(too_many)})
    assert httpx_mock.get_requests() == []


async def test_filter_widened_types_dates_ints_or_not(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("rp_page.json")))
    httpx_mock.add_response(**json_response(load("projects_page.json")))
    await client.research_products.search(
        ResearchProductsFilters(
            type=["publication", "dataset"],
            from_publication_date=date(2024, 1, 15),
            impact_citation_count=10,
        )
    )
    await client.projects.search(
        ProjectsFilters(project_status="!completed", start_year=[2023, 2024])
    )
    rp_parts = set(params_of(httpx_mock.get_requests()[0])["filter"].split(","))
    assert rp_parts == {
        "type:publication|dataset",
        "from_publication_date:2024-01-15",
        "impact.citation_count:10",
    }
    pr_parts = set(params_of(httpx_mock.get_requests()[1])["filter"].split(","))
    assert pr_parts == {"project_status:!completed", "start_year:2023|2024"}


async def test_sort_whitespace_and_empty_handling(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("rp_page.json")))
    httpx_mock.add_response(**json_response(load("rp_page.json")))
    await client.research_products.search(sort=" citation_count : DESC ")
    await client.research_products.search(sort=" , ")
    assert params_of(httpx_mock.get_requests()[0])["sort"] == "citation_count:desc"
    assert "sort" not in params_of(httpx_mock.get_requests()[1])


async def test_facets_and_group_by_reject_empty_fields(httpx_mock, client):
    with pytest.raises(ConfigurationError, match="at least one field"):
        await client.research_products.facets()
    with pytest.raises(ConfigurationError, match="non-empty field"):
        await client.research_products.group_by("   ")
    assert httpx_mock.get_requests() == []


async def test_links_dict_filter_strips_none(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("links_page.json")))
    await client.research_products.search_links(
        {"sourcePid": "10.1234/x", "targetPid": None}
    )
    params = params_of(httpx_mock.get_request())
    assert params["sourcePid"] == "10.1234/x"
    assert "targetPid" not in params


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
        httpx_mock.add_response(**json_response(load("rp_page.json")))
        httpx_mock.add_response(**json_response(load("scholix_page.json")))
        await client.research_products.search()
        await client.request("GET", "/v4/research-products", timeout=5.0)
        await client.scholix.search_links(None, page_size=5)
    graph_params = params_of(httpx_mock.get_requests()[0])
    leading_slash_params = params_of(httpx_mock.get_requests()[1])
    scholix_params = params_of(httpx_mock.get_requests()[2])
    assert graph_params["mailto"] == "team@example.org"
    assert leading_slash_params["mailto"] == "team@example.org"
    assert "mailto" not in scholix_params


async def test_request_forwards_retry_flag(httpx_mock, client):
    httpx_mock.add_response(status_code=503)
    with pytest.raises(APIError):
        await client.request("GET", "v4/research-products", retry=False)
    assert len(httpx_mock.get_requests()) == 1

    httpx_mock.add_response(status_code=503)
    httpx_mock.add_response(**json_response(load("rp_page.json")))
    response = await client.request("POST", "v4/research-products", retry=True)
    assert response.status_code == 200
    assert len(httpx_mock.get_requests()) == 3
