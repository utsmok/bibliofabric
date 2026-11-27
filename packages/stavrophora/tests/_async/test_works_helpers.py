"""WorksResource extras: batch DOI lookup, facets, sample, agency."""

import pytest
from bibliofabric.exceptions import ConfigurationError, ValidationError

from .conftest import fixture, work, works_envelope


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
    assert request.url.params["rows"] == "0"
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
    assert (
        request.url.raw_path.split(b"?")[0] == b"/v1/works/10.1038%2Fnature12373/agency"
    )
    assert agency.doi == "10.1038/nature12373"
    assert agency.agency.id == "crossref"
    assert agency.agency.label == "Crossref"


async def test_exists_sends_head_and_reports_404(httpx_mock, client):
    httpx_mock.add_response(status_code=200)
    assert await client.works.exists("https://doi.org/10.1038/Nature12373") is True
    request = httpx_mock.get_requests()[0]
    assert request.method == "HEAD"
    assert request.url.path == "/v1/works/10.1038/nature12373"
    assert request.url.raw_path.split(b"?")[0] == b"/v1/works/10.1038%2Fnature12373"

    httpx_mock.add_response(status_code=404, text="Resource not found.")
    assert await client.works.exists("10.9999/nope") is False


async def test_latest_version_follows_updated_by_to_the_head_record(httpx_mock, client):
    httpx_mock.add_response(json=fixture("work_updated.json"))
    httpx_mock.add_response(json=fixture("work_version.json"))
    latest = await client.works.latest_version("10.12688/f1000research.141553.1")
    assert [r.url.path for r in httpx_mock.get_requests()] == [
        "/v1/works/10.12688/f1000research.141553.1",
        "/v1/works/10.12688/f1000research.141553.3",
    ]
    assert latest.doi == "10.12688/f1000research.141553.3"


async def test_latest_version_returns_records_without_updates_unchanged(
    httpx_mock, client
):
    httpx_mock.add_response(json=fixture("work_version.json"))
    latest = await client.works.latest_version("10.12688/f1000research.141553.3")
    assert len(httpx_mock.get_requests()) == 1
    assert latest.doi == "10.12688/f1000research.141553.3"


async def test_latest_version_falls_back_to_date_parts_and_breaks_redirect_cycles(
    httpx_mock, client
):
    first = {
        "status": "ok",
        "message-type": "work",
        "message": {
            "DOI": "10.1/canonical",
            "title": ["V1"],
            "updated-by": [
                {
                    "DOI": "10.1/v2",
                    "type": "new_version",
                    "updated": {"date-parts": [[2024, 1, 10]]},
                },
                {
                    "DOI": "10.1/v3",
                    "type": "new_version",
                    "updated": {"date-parts": [[2024, 5, 1]]},
                },
            ],
        },
    }
    third = {
        "status": "ok",
        "message-type": "work",
        "message": {
            "DOI": "10.1/v3",
            "title": ["V3"],
            "updated-by": [
                {
                    "DOI": "10.1/canonical",
                    "type": "new_version",
                    "updated": {"date-parts": [[2024, 6, 1]]},
                },
            ],
        },
    }
    httpx_mock.add_response(json=first)
    httpx_mock.add_response(json=third)
    latest = await client.works.latest_version("10.1/alias")
    assert latest.doi == "10.1/v3"
    assert len(httpx_mock.get_requests()) == 2


async def test_latest_version_ignores_retractions_and_corrections_by_default(
    httpx_mock, client
):
    record = {
        "status": "ok",
        "message-type": "work",
        "message": {
            "DOI": "10.1/orig",
            "title": ["Original"],
            "updated-by": [
                {
                    "DOI": "10.1/retraction",
                    "type": "retraction",
                    "updated": {"timestamp": 1712707200000},
                },
                {
                    "DOI": "10.1/correction",
                    "type": "correction",
                    "updated": {"timestamp": 1712000000000},
                },
            ],
        },
    }
    httpx_mock.add_response(json=record)
    latest = await client.works.latest_version("10.1/orig")
    assert latest.doi == "10.1/orig"
    assert len(httpx_mock.get_requests()) == 1


async def test_latest_version_follows_new_edition_and_allows_unfiltered_updates(
    httpx_mock, client
):
    first = {
        "status": "ok",
        "message-type": "work",
        "message": {
            "DOI": "10.1/v1",
            "title": ["Edition 1"],
            "updated-by": [
                {
                    "DOI": "10.1/ed2",
                    "type": "new_edition",
                    "updated": {"timestamp": 1700000000000},
                },
                {
                    "DOI": "10.1/retract",
                    "type": "retraction",
                    "updated": {"timestamp": 1720000000000},
                },
            ],
        },
    }
    second = {
        "status": "ok",
        "message-type": "work",
        "message": {"DOI": "10.1/ed2", "title": ["Edition 2"]},
    }
    retraction = {
        "status": "ok",
        "message-type": "work",
        "message": {"DOI": "10.1/retract", "title": ["Retraction notice"]},
    }
    httpx_mock.add_response(json=first)
    httpx_mock.add_response(json=second)
    latest = await client.works.latest_version("10.1/v1")
    assert latest.doi == "10.1/ed2"

    httpx_mock.add_response(json=first)
    httpx_mock.add_response(json=retraction)
    all_updates = await client.works.latest_version("10.1/v1", update_types=None)
    assert all_updates.doi == "10.1/retract"


async def test_agency_wraps_validation_errors(httpx_mock, client):
    httpx_mock.add_response(
        json={
            "status": "ok",
            "message-type": "work-agency",
            "message": {"DOI": "10.1/x", "agency": "not-an-object"},
        }
    )
    with pytest.raises(ValidationError, match="WorkAgency") as exc_info:
        await client.works.agency("10.1/x")
    assert exc_info.value.model_name == "WorkAgency"
    assert isinstance(exc_info.value.raw, dict)
    assert exc_info.value.raw["DOI"] == "10.1/x"


async def test_batch_get_by_doi_on_error_skip(httpx_mock, client):
    bad = work("10.1/bad")
    bad["issued"] = 12345
    httpx_mock.add_response(json=works_envelope([bad, work("10.1/good")]))
    failures: list = []
    result = await client.works.batch_get_by_doi(
        ["10.1/bad", "10.1/good"], on_error="skip", failures=failures
    )
    assert list(result) == ["10.1/good"]
    assert len(failures) == 1
