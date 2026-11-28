"""Request shape and response parsing for the search resource (mocked)."""

import pytest
from bibliofabric.exceptions import ConfigurationError
from europaea import SearchResult

from ..conftest import lite_record, load_fixture, search_envelope


async def test_search_sends_europepmc_params(httpx_mock, client):
    httpx_mock.add_response(json=search_envelope([lite_record()], hit_count=5_670_999))

    page = await client.search.search(query="cancer", result_type="lite", synonym=True)

    request = httpx_mock.get_requests()[0]
    assert request.url.path == "/europepmc/webservices/rest/search"
    assert request.url.params["query"] == "cancer"
    assert request.url.params["format"] == "json"
    assert request.url.params["resultType"] == "lite"
    assert request.url.params["synonym"] == "true"
    assert request.url.params["pageSize"] == "25"
    assert request.headers["Accept"] == "application/json"
    assert page.total == 5_670_999
    assert isinstance(page.results[0], SearchResult)


async def test_search_page_size_is_capped_at_1000(httpx_mock, client):
    httpx_mock.add_response(json=search_envelope([lite_record()]))
    await client.search.search(query="cancer", page_size=5000)
    assert httpx_mock.get_requests()[0].url.params["pageSize"] == "1000"


async def test_search_cursor_paging(httpx_mock, client):
    first = load_fixture("search_cursor_page1.json")
    httpx_mock.add_response(json=first)

    page = await client.search.search(query="cancer", cursor=first["nextCursorMark"])

    request = httpx_mock.get_requests()[0]
    assert request.url.params["cursorMark"] == first["nextCursorMark"]
    assert page.next_cursor == first["nextCursorMark"]
    assert page.total == first["hitCount"]


async def test_search_iterate_stops_on_repeated_cursor(httpx_mock, client):
    last_page = search_envelope([lite_record()], next_cursor_mark="SAME")
    done = search_envelope([], next_cursor_mark="SAME")
    httpx_mock.add_response(json=last_page)
    httpx_mock.add_response(json=done)

    records = [
        record async for record in client.search.iterate(query="cancer", page_size=25)
    ]

    requests = httpx_mock.get_requests()
    assert len(requests) == 2
    assert requests[0].url.params["cursorMark"] == "*"
    assert requests[0].url.params["pageSize"] == "25"
    assert requests[1].url.params["cursorMark"] == "SAME"
    assert len(records) == 1


async def test_search_sort_is_sent_verbatim(httpx_mock, client):
    httpx_mock.add_response(json=search_envelope([lite_record()]))
    await client.search.search(query="cancer", sort="P_PDATE_D desc")
    assert httpx_mock.get_requests()[0].url.params["sort"] == "P_PDATE_D desc"


async def test_search_rejects_unknown_sort_field(client):
    with pytest.raises(ConfigurationError):
        client.search._check_sort("banana desc")


async def test_fields_endpoint(httpx_mock, client):
    httpx_mock.add_response(json=load_fixture("fields.json"))
    fields = await client.search.fields()
    assert "ACCESSION_ID" in fields
    request = httpx_mock.get_requests()[0]
    assert request.url.path == "/europepmc/webservices/rest/fields"


async def test_preprints_scope_the_query(httpx_mock, client):
    httpx_mock.add_response(json=search_envelope([lite_record(source="PPR")]))
    await client.preprints.search(query="nanodiamond")
    assert (
        httpx_mock.get_requests()[0].url.params["query"] == "SRC:PPR AND (nanodiamond)"
    )


async def test_preprints_without_query_searches_the_source(httpx_mock, client):
    httpx_mock.add_response(json=search_envelope([lite_record(source="PPR")]))
    await client.preprints.search()
    assert httpx_mock.get_requests()[0].url.params["query"] == "SRC:PPR"


async def test_search_post_sends_form_body(httpx_mock, client):
    httpx_mock.add_response(json=search_envelope([lite_record()], hit_count=42))

    page = await client.search.search_post(
        query="cancer", result_type="lite", synonym=True, cursor="AoIIP9Pb"
    )

    request = httpx_mock.get_requests()[0]
    assert request.url.path == "/europepmc/webservices/rest/searchPOST"
    body = request.content.decode()
    assert "query=cancer" in body
    assert "resultType=lite" in body
    assert "synonym=true" in body
    assert "cursorMark=AoIIP9Pb" in body
    assert "pageSize=25" in body
    assert request.headers["Content-Type"].startswith(
        "application/x-www-form-urlencoded"
    )
    assert page.total == 42
    assert isinstance(page.results[0], SearchResult)


async def test_search_post_iterate_stops_on_repeated_cursor(httpx_mock, client):
    last_page = search_envelope([lite_record()], next_cursor_mark="SAME")
    done = search_envelope([], next_cursor_mark="SAME")
    httpx_mock.add_response(json=last_page)
    httpx_mock.add_response(json=done)

    records = [
        record
        async for record in client.search.iterate_post(query="cancer", page_size=2)
    ]

    requests = httpx_mock.get_requests()
    assert len(requests) == 2
    assert requests[0].url.path == "/europepmc/webservices/rest/searchPOST"
    assert len(records) == 1
