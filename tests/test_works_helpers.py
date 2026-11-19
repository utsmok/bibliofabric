"""WorksResource extras: batch DOI lookup, facets, sample, agency."""

import pytest
from bibliofabric.exceptions import ConfigurationError

from tests.conftest import fixture, work, works_envelope


def chunk_filter(params) -> list[str]:
    return [entry.removeprefix("doi:") for entry in params["filter"].split(",")]


async def test_batch_get_by_doi_splits_into_chunks(httpx_mock, client):
    dois = [f"10.1000/test{i:03d}" for i in range(55)]
    items = [work(doi) for doi in dois]
    httpx_mock.add_response(json=works_envelope(items))
    httpx_mock.add_response(json=works_envelope(items))
    result = await client.works.batch_get_by_doi(dois)

    requests = httpx_mock.get_requests()
    assert len(requests) == 2
    assert chunk_filter(requests[0].url.params) == dois[:50]
    assert chunk_filter(requests[1].url.params) == dois[50:]
    assert requests[0].url.params["rows"] == "50"
    assert requests[1].url.params["rows"] == "5"
    assert set(result) == set(dois)
    assert result["10.1000/test000"].doi == "10.1000/test000"


async def test_batch_get_by_doi_normalizes_and_deduplicates(httpx_mock, client):
    httpx_mock.add_response(json=works_envelope([work("10.1038/nature12373")]))
    result = await client.works.batch_get_by_doi(
        [
            "10.1038/NATURE12373",
            "https://doi.org/10.1038/nature12373",
            "10.1038/nature12373",
        ]
    )
    request = httpx_mock.get_requests()[0]
    assert chunk_filter(request.url.params) == ["10.1038/nature12373"]
    assert request.url.params["rows"] == "1"
    assert list(result) == ["10.1038/nature12373"]


async def test_batch_get_by_doi_drops_missing_dois(httpx_mock, client):
    httpx_mock.add_response(json=works_envelope([work("10.1/found")]))
    result = await client.works.batch_get_by_doi(["10.1/found", "10.1/missing"])
    assert set(result) == {"10.1/found"}


async def test_facets_flatten_the_nested_values_shape(httpx_mock, client):
    httpx_mock.add_response(json=fixture("facet_archive.json"))
    facets = await client.works.facets(query="climate", facets=("archive",))
    request = httpx_mock.get_requests()[0]
    assert request.url.params["facet"] == "archive:*"
    assert request.url.params["rows"] == "1"
    assert request.url.params["offset"] == "0"
    assert facets == {
        "archive": {
            "Portico": 39391,
            "Internet Archive": 941,
            "CLOCKSS": 585,
            "LOCKSS": 375,
            "DWT": 112,
            "KB": 108,
            "BL": 9,
        }
    }


async def test_facets_count_caps_values_per_facet(httpx_mock, client):
    httpx_mock.add_response(json=fixture("facet_archive.json"))
    await client.works.facets(facets=("archive", "type"), count=500)
    assert httpx_mock.get_requests()[0].url.params["facet"] == "archive:500,type:500"


@pytest.mark.parametrize("count", [0, 1001])
async def test_facets_count_out_of_range_is_rejected(client, count):
    with pytest.raises(ConfigurationError, match="between 1 and 1000"):
        await client.works.facets(count=count)


async def test_sample_sends_sample_param_without_paging(httpx_mock, client):
    httpx_mock.add_response(json=works_envelope([work("10.1/drawn")]))
    page = await client.works.sample(5)
    params = httpx_mock.get_requests()[0].url.params
    assert params["sample"] == "5"
    assert "rows" not in params
    assert "offset" not in params
    assert [item.doi for item in page.results] == ["10.1/drawn"]


@pytest.mark.parametrize("n", [0, 101])
async def test_sample_past_100_is_rejected(client, n):
    with pytest.raises(ConfigurationError, match="caps sample at 100"):
        await client.works.sample(n)


async def test_agency_requests_the_agency_route(httpx_mock, client):
    httpx_mock.add_response(json=fixture("agency.json"))
    agency = await client.works.agency("https://doi.org/10.1038/Nature12373")
    request = httpx_mock.get_requests()[0]
    assert request.url.path == "/v1/works/10.1038/nature12373/agency"
    assert agency.doi == "10.1038/nature12373"
    assert agency.agency.id == "crossref"
    assert agency.agency.label == "Crossref"
