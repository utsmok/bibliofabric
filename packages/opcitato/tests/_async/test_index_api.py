"""Outgoing request shape and row handling of the Index API client."""

import httpx
import pytest
from bibliofabric.exceptions import (
    APIError,
    ConfigurationError,
    ValidationError,
)
from opcitato import OpcitatoClient

from ..conftest import count_rows, load_fixture, load_fixture_json

#: A real DOI whose suffix carries characters that need percent-encoding in a
#: URL path (parentheses, angle brackets, colons, a semicolon).
SICI_DOI = "doi:10.1002/(SICI)1097-4636(199823)43:3<338::AID-JBM16>3.0.CO;2-B"


def last_request(httpx_mock):
    return httpx_mock.get_requests()[-1]


def params_of(request):
    return dict(request.url.params)


async def test_citations_request_and_rows(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture_json("citations.json"))
    rows = await client.index.citations("doi:10.1108/jd-12-2013-0166")
    request = last_request(httpx_mock)
    assert request.url.path == "/index/v2/citations/doi:10.1108/jd-12-2013-0166"
    assert request.headers["accept"] == "application/json"
    assert [row.oci for row in rows] == [
        "06012708740-06180334099",
        "06013267230-06180334099",
        "06013789762-06180334099",
    ]
    assert rows[0].cited_identifiers[1].scheme == "doi"


async def test_citations_sends_repeated_params_and_encoded_values(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture_json("empty.json"))
    await client.index.citations(
        "doi:10.1108/jd-12-2013-0166",
        require=["creation", "timespan"],
        filter="creation:>2019-12",
        sort="desc(creation)",
    )
    params = last_request(httpx_mock).url.params
    assert params.get_list("require") == ["creation", "timespan"]
    assert params["filter"] == "creation:>2019-12"
    assert params["sort"] == "desc(creation)"
    assert params["format"] == "json"


async def test_citations_csv_parses_into_the_same_model(client, httpx_mock):
    httpx_mock.add_response(
        text=load_fixture("citations.csv"),
        headers={"content-type": "text/csv; charset=utf-8"},
    )
    rows = await client.index.citations("doi:10.1108/jd-12-2013-0166", format="csv")
    assert params_of(last_request(httpx_mock))["format"] == "csv"
    assert rows[0].oci == "06012708740-06180334099"
    assert rows[0].journal_sc == "no"


async def test_references_request(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture_json("references.json"))
    rows = await client.index.references("omid:br/06101801781")
    assert (
        last_request(httpx_mock).url.path == "/index/v2/references/omid:br/06101801781"
    )
    assert [row.oci for row in rows] == [
        "06101801781-06101802023",
        "06101801781-061202127742",
        "06101801781-061202127823",
    ]
    assert rows[0].journal_sc == "yes"


async def test_references_csv_parses_into_the_same_model(client, httpx_mock):
    httpx_mock.add_response(
        text=load_fixture("references.csv"),
        headers={"content-type": "text/csv"},
    )
    rows = await client.index.references("doi:10.7717/peerj-cs.421", format="csv")
    assert params_of(last_request(httpx_mock))["format"] == "csv"
    assert [row.timespan for row in rows] == ["P2Y5M21D", "P0Y3M6D"]


async def test_special_characters_of_an_id_are_percent_encoded(client, httpx_mock):
    httpx_mock.add_response(json=count_rows(998))
    count = await client.index.citation_count(SICI_DOI)
    request = last_request(httpx_mock)
    assert count == 998
    assert request.url.path == "/index/v2/citation-count/" + SICI_DOI
    # Parentheses, angle brackets, and the semicolon are encoded; the colon
    # and the slash are legal in a path segment and stay readable.
    assert request.url.raw_path == (
        b"/index/v2/citation-count/doi:10.1002/%28SICI%291097-4636%28199823%2943"
        b":3%3C338::AID-JBM16%3E3.0.CO%3B2-B"
    )


async def test_hash_and_question_mark_do_not_split_the_path(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture_json("empty.json"))
    await client.index.citations("doi:10.1000/a#b?c")
    request = last_request(httpx_mock)
    assert request.url.path == "/index/v2/citations/doi:10.1000/a#b?c"
    assert (
        request.url.raw_path == b"/index/v2/citations/doi:10.1000/a%23b%3Fc?format=json"
    )
    assert dict(request.url.params) == {"format": "json"}


async def test_citation_by_oci_strips_the_prefix(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture_json("citation.json"))
    row = await client.index.citation("oci:06101801781-06180334099")
    assert (
        last_request(httpx_mock).url.path
        == "/index/v2/citation/06101801781-06180334099"
    )
    assert row is not None
    assert row.timespan == "P6Y0M1D"


async def test_citation_unknown_returns_none(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture_json("empty.json"))
    assert await client.index.citation("999999999-999999999") is None


async def test_citation_count_reads_the_string_number(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture_json("citation_count.json"))
    assert await client.index.citation_count("doi:10.1108/jd-12-2013-0166") == 57
    assert (
        last_request(httpx_mock).url.path
        == "/index/v2/citation-count/doi:10.1108/jd-12-2013-0166"
    )


async def test_citation_count_reads_a_zero_row(client, httpx_mock):
    httpx_mock.add_response(json=count_rows(0))
    assert await client.index.citation_count("doi:10.9999/nonexistent.000") == 0


async def test_citation_count_of_an_empty_list_is_none(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture_json("empty.json"))
    assert await client.index.citation_count("doi:10.9999/nonexistent.000") is None


async def test_reference_count_and_venue_count_paths(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture_json("reference_count.json"))
    httpx_mock.add_response(json=load_fixture_json("venue_citation_count.json"))
    assert await client.index.reference_count("doi:10.7717/peerj-cs.421") == 37
    assert await client.index.venue_citation_count("issn:0138-9130") == 107750
    assert (
        last_request(httpx_mock).url.path
        == "/index/v2/venue-citation-count/issn:0138-9130"
    )


async def test_count_of_a_body_that_is_not_a_list_raises(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture_json("citation_count.json")[0])
    with pytest.raises(ConfigurationError, match="instead of a list"):
        await client.index.citation_count("doi:10.1108/jd-12-2013-0166")


async def test_rows_of_a_body_that_is_not_a_list_raise(client, httpx_mock):
    httpx_mock.add_response(json={"rows": load_fixture_json("citations.json")})
    with pytest.raises(ConfigurationError, match="instead of a list"):
        await client.index.citations("doi:10.1108/jd-12-2013-0166")


async def test_a_row_that_fails_validation_raises_validation_error(client, httpx_mock):
    httpx_mock.add_response(json=["not a row"])
    with pytest.raises(ValidationError, match="Failed to validate Citation"):
        await client.index.citations("doi:10.1108/jd-12-2013-0166")


@pytest.mark.parametrize(
    ("kwargs", "fragment"),
    [
        ({"format": "xml"}, "format"),
        ({"sort": "creation"}, "sort"),
        ({"sort": "sideways(creation)"}, "sort"),
        ({"filter": [""]}, "non-empty"),
        ({"require": "  "}, "non-empty"),
    ],
)
async def test_bad_row_parameters_raise_without_request(
    client, httpx_mock, kwargs, fragment
):
    with pytest.raises(ConfigurationError, match=fragment):
        await client.index.citations("doi:10.1108/jd-12-2013-0166", **kwargs)
    assert not httpx_mock.get_requests()


@pytest.mark.parametrize(
    ("id", "fragment"),
    [("10.1108/jd-12-2013-0166", "scheme:value"), ("openalex:W1", "openalex")],
)
async def test_unprefixed_ids_raise_without_request(client, httpx_mock, id, fragment):
    with pytest.raises(ConfigurationError, match=fragment):
        await client.index.citations(id)
    assert not httpx_mock.get_requests()


@pytest.mark.parametrize("fixture", ["error_400_id.txt", "error_400_scheme.txt"])
async def test_400_body_raises_api_error(client, httpx_mock, fixture):
    httpx_mock.add_response(
        text=load_fixture(fixture),
        status_code=400,
        headers={"content-type": "text/plain"},
    )
    with pytest.raises(APIError, match="not valid"):
        await client.index.citations("doi:10.1108/jd-12-2013-0166")


async def test_a_prepared_http_client_carries_its_own_headers(settings, httpx_mock):
    """The documented way to send an Access Token: a caller-owned client."""
    httpx_mock.add_response(json=count_rows(12))
    async with (
        httpx.AsyncClient(headers={"authorization": "a-token"}) as prepared,
        OpcitatoClient(settings=settings, http_client=prepared) as client,
    ):
        count = await client.index.citation_count("doi:10.1108/jd-12-2013-0166")
    assert count == 12
    headers = last_request(httpx_mock).headers
    assert headers["authorization"] == "a-token"
    assert headers["accept"] == "application/json"
