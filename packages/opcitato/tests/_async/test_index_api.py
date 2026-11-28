"""Outgoing request shape and row handling of the Index API client."""

import pytest
from bibliofabric.exceptions import APIError, ConfigurationError

from ..conftest import (
    citation,
    count_rows,
    load_fixture,
    load_fixture_json,
)


def last_request(httpx_mock):
    return httpx_mock.get_requests()[-1]


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
    httpx_mock.add_response(json=[])
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


def params_of(request):
    return dict(request.url.params)


async def test_references_request(client, httpx_mock):
    httpx_mock.add_response(json=[citation()])
    rows = await client.index.references("omid:br/06101801781")
    assert (
        last_request(httpx_mock).url.path == "/index/v2/references/omid:br/06101801781"
    )
    assert rows[0].oci == "06101801781-06180334099"


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
    httpx_mock.add_response(json=[])
    assert await client.index.citation("999999999-999999999") is None


async def test_citation_count_reads_the_string_number(client, httpx_mock):
    httpx_mock.add_response(json=count_rows(57))
    assert await client.index.citation_count("doi:10.1108/jd-12-2013-0166") == 57
    assert (
        last_request(httpx_mock).url.path
        == "/index/v2/citation-count/doi:10.1108/jd-12-2013-0166"
    )


async def test_citation_count_unknown_returns_none(client, httpx_mock):
    httpx_mock.add_response(json=[])
    assert await client.index.citation_count("doi:10.9999/nonexistent.000") is None


async def test_reference_count_and_venue_count_paths(client, httpx_mock):
    httpx_mock.add_response(json=count_rows(37))
    httpx_mock.add_response(json=count_rows(107750))
    assert await client.index.reference_count("doi:10.7717/peerj-cs.421") == 37
    assert await client.index.venue_citation_count("issn:0138-9130") == 107750
    assert (
        last_request(httpx_mock).url.path
        == "/index/v2/venue-citation-count/issn:0138-9130"
    )


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


async def test_400_body_raises_api_error(client, httpx_mock):
    httpx_mock.add_response(
        text=load_fixture("error_400_id.txt"),
        status_code=400,
        headers={"content-type": "text/plain"},
    )
    with pytest.raises(APIError, match="not valid"):
        await client.index.citations("doi:10.1108/jd-12-2013-0166")
