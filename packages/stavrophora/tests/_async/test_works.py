"""The /works route: request shape and parsing of real payloads."""

import pytest
from bibliofabric.exceptions import ConfigurationError
from stavrophora import WorksFilters

from .conftest import fixture, work, works_envelope


async def test_search_request_shape(httpx_mock, client):
    httpx_mock.add_response(json=fixture("works_list.json"))
    await client.works.search(
        WorksFilters(has_abstract=True, from_pub_date="2020-01-01"),
        query="climate change",
        sort="is-referenced-by-count:desc",
        select=["DOI", "title"],
        page=2,
        page_size=50,
    )
    params = httpx_mock.get_requests()[0].url.params
    assert httpx_mock.get_requests()[0].url.path == "/v1/works"
    assert params["query"] == "climate change"
    assert params["filter"] == "from-pub-date:2020-01-01,has-abstract:true"
    assert params["sort"] == "is-referenced-by-count"
    assert params["order"] == "desc"
    assert params["select"] == "DOI,title"
    assert params["rows"] == "50"
    assert params["offset"] == "50"


async def test_sort_without_direction_omits_order(httpx_mock, client):
    httpx_mock.add_response(json=works_envelope([]))
    await client.works.search(sort="score")
    params = httpx_mock.get_requests()[0].url.params
    assert params["sort"] == "score"
    assert "order" not in params


async def test_filter_lists_use_repeated_key_or_syntax(httpx_mock, client):
    httpx_mock.add_response(json=works_envelope([]))
    await client.works.search({"doi": ["10.1/a", "10.2/b"], "type": "journal-article"})
    params = httpx_mock.get_requests()[0].url.params
    assert params["filter"] == "doi:10.1/a,doi:10.2/b,type:journal-article"


async def test_filter_aliases_serialize_to_kebab_case(httpx_mock, client):
    httpx_mock.add_response(json=works_envelope([]))
    await client.works.search(WorksFilters(ror_id="03d02034x", gte_citation=50))
    assert (
        httpx_mock.get_requests()[0].url.params["filter"]
        == "ror-id:03d02034x,gte-citation:50"
    )


async def test_query_title_escape_hatch(httpx_mock, client):
    httpx_mock.add_response(json=works_envelope([]))
    await client.works.search(params={"query.title": "climate"})
    assert httpx_mock.get_requests()[0].url.params["query.title"] == "climate"


async def test_multiple_sort_fields_are_rejected(client):
    with pytest.raises(ConfigurationError, match="single sort field"):
        await client.works.search(sort=["score", "issued"])


async def test_offset_window_boundary_is_allowed(httpx_mock, client):
    httpx_mock.add_response(json=works_envelope([]))
    await client.works.search(page_size=1000, page=10)
    assert httpx_mock.get_requests()[0].url.params["offset"] == "9000"


async def test_offset_window_past_10000_is_rejected(client):
    with pytest.raises(ConfigurationError, match="10000"):
        await client.works.search(page_size=1000, page=11)


async def test_search_parses_real_payload(httpx_mock, client):
    httpx_mock.add_response(json=fixture("works_list.json"))
    page = await client.works.search(query="climate change", page_size=2)
    assert page.total == 1458602
    assert len(page.results) == 2
    first = page.results[0]
    assert first.doi == "10.1093/hesc/9780198807506.003.0005"
    assert first.publisher == "Oxford University Press"
    assert first.score == pytest.approx(19.43201)
    assert first.issued.year == 2023
    assert first.is_referenced_by_count == 1
    assert first.primary_title.startswith("Climate Change")


async def test_search_meta_keeps_envelope_extras(httpx_mock, client):
    httpx_mock.add_response(json=fixture("works_list.json"))
    page = await client.works.search(query="climate change")
    assert page.meta["total-results"] == 1458602
    assert "items" not in page.meta


async def test_get_parses_real_single_work(httpx_mock, client):
    httpx_mock.add_response(json=fixture("work_get.json"))
    work_ = await client.works.get("https://doi.org/10.1038/Nature12373")
    request = httpx_mock.get_requests()[0]
    assert request.url.path == "/v1/works/10.1038/nature12373"
    assert work_.doi == "10.1038/nature12373"
    assert work_.title == ["Nanometre-scale thermometry in a living cell"]
    assert work_.member == "297"
    assert work_.prefix == "10.1038"
    assert work_.is_referenced_by_count == 1870
    assert work_.references_count == 30
    assert work_.score == 1
    assert work_.source == "Crossref"
    assert work_.journal_issue.issue == "7460"
    assert work_.license[0].delay_in_days == 0
    assert work_.reference[0].doi_asserted_by == "publisher"
    assert work_.author[0].role[0].role == "author"


async def test_get_parses_drift_fixed_funder_fields(httpx_mock, client):
    httpx_mock.add_response(json=fixture("funder_work_item.json"))
    work_ = await client.works.get("10.1109/ner49283.2021.9441222")
    funder = work_.funder[0]
    assert funder.doi == "10.13039/100000002"
    assert funder.doi_asserted_by == "publisher"
    assert funder.award == ["MH122023"]
    assert funder.award_info[0].award_number == ["MH122023"]
    assert funder.id[0].id_type == "DOI"


async def test_get_parses_event_sponsor_list(httpx_mock, client):
    """ACM proceedings print ``event.sponsor`` as a list (live 2026-11-27)."""
    httpx_mock.add_response(json=fixture("work_event_sponsor_list.json"))
    work_ = await client.works.get("10.1145/1388969.1389056")
    assert work_.event is not None
    assert work_.event.acronym == "GECCO08"
    assert work_.event.sponsor == [
        "SIGEVO ACM Special Interest Group on Genetic and Evolutionary Computation",
        "ACM Association for Computing Machinery",
    ]


async def test_search_keeps_a_page_with_an_event_sponsor_list(httpx_mock, client):
    sponsored = fixture("work_event_sponsor_list.json")["message"]
    httpx_mock.add_response(
        json=works_envelope([work("10.1/first"), sponsored, work("10.1/last")])
    )
    page = await client.works.search(query="introduction to genetic algorithms")
    assert [item.doi for item in page.results] == [
        "10.1/first",
        "10.1145/1388969.1389056",
        "10.1/last",
    ]


async def test_event_sponsor_string_becomes_a_one_item_list(httpx_mock, client):
    single = work("10.1/sponsor")
    single["event"] = {"name": "GECCO '11", "sponsor": "ACM"}
    httpx_mock.add_response(json=works_envelope([single]))
    page = await client.works.search()
    assert page.results[0].event.sponsor == ["ACM"]


async def test_404_raises_not_found_without_retry(httpx_mock, client):
    httpx_mock.add_response(status_code=404, json="Resource not found.")
    with pytest.raises(Exception, match="404") as exc_info:
        await client.works.get("10.1/missing")
    assert exc_info.type.__name__ == "NotFoundError"
    assert len(httpx_mock.get_requests()) == 1


async def test_429_with_retry_after_zero_is_retried(httpx_mock, client):
    httpx_mock.add_response(status_code=429, headers={"Retry-After": "0"}, json={})
    httpx_mock.add_response(json=fixture("work_get.json"))
    work_ = await client.works.get("10.1038/nature12373")
    assert work_.doi == "10.1038/nature12373"
    assert len(httpx_mock.get_requests()) == 2


async def test_403_raises_auth_error_without_retry(httpx_mock, client):
    httpx_mock.add_response(status_code=403, json={})
    with pytest.raises(Exception, match="403") as exc_info:
        await client.works.search()
    assert exc_info.type.__name__ == "AuthError"
    assert len(httpx_mock.get_requests()) == 1


def _bad_work() -> dict:
    bad = work("10.1/broken")
    bad["issued"] = 12345  # date object expected, not an int
    return bad


async def test_iterate_invalid_record_raises_validation_error(httpx_mock, client):
    httpx_mock.add_response(json=works_envelope([_bad_work()]))
    with pytest.raises(Exception, match="Work") as exc_info:
        async for _ in client.works.iterate():
            pass
    assert exc_info.type.__name__ == "ValidationError"
    assert exc_info.value.raw["DOI"] == "10.1/broken"


async def test_iterate_on_error_skip_records_failures(httpx_mock, client):
    httpx_mock.add_response(json=works_envelope([_bad_work(), work("10.1/ok")]))
    failures: list = []
    collected = [
        item async for item in client.works.iterate(on_error="skip", failures=failures)
    ]
    assert [item.doi for item in collected] == ["10.1/ok"]
    assert len(failures) == 1
    assert failures[0][0]["DOI"] == "10.1/broken"
