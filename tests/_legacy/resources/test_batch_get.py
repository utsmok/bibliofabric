"""Tests for batch_get and auto-generated batch_get_by_* methods."""

import pytest

from stavrophora.resources.works_client import WorksClient

from .conftest import _mock_response

# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

WORK_A = {"DOI": "10.1234/alpha", "title": ["Work A"]}
WORK_B = {"DOI": "10.5678/beta", "title": ["Work B"]}

RESULTS_A_B = {"message": {"total-results": 2, "items": [WORK_A, WORK_B]}}


@pytest.fixture
def works_client(mock_api_client):
    return WorksClient(mock_api_client)


def _params(mock_api_client, index=-1):
    return mock_api_client.request.call_args_list[index].kwargs["params"]


# ---------------------------------------------------------------------------
# batch_get — core functionality
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_batch_get_empty_input(works_client):
    assert await works_client.batch_get([]) == {}


@pytest.mark.asyncio
async def test_batch_get_single_batch(works_client, mock_api_client):
    """Single batch (≤50 items) → one search call with repeated doi: keys."""
    mock_api_client.request.return_value = _mock_response(RESULTS_A_B)
    result = await works_client.batch_get(["10.1234/alpha", "10.5678/beta"])
    assert set(result) == {"10.1234/alpha", "10.5678/beta"}
    assert mock_api_client.request.await_count == 1
    filter_str = _params(mock_api_client)["filter"]
    assert filter_str == "doi:10.1234/alpha,doi:10.5678/beta"


@pytest.mark.asyncio
async def test_batch_get_partial_results(works_client, mock_api_client):
    """Only some DOIs found — missing ones absent from result."""
    mock_api_client.request.return_value = _mock_response(RESULTS_A_B)
    result = await works_client.batch_get(["10.1234/alpha", "10.5678/does_not_exist"])
    assert "10.1234/alpha" in result
    assert "10.5678/does_not_exist" not in result


@pytest.mark.asyncio
async def test_batch_get_multiple_batches(works_client, mock_api_client):
    """More than batch_size identifiers → multiple search calls."""
    ids = [f"10.1234/{i:03d}" for i in range(60)]
    calls = []

    async def fake_request(_method, _path, *, params=None, **_kw):
        calls.append(params)
        dois = (params or {})["filter"].removeprefix("doi:").split(",")
        items = [{"DOI": d} for d in dois]
        return _mock_response(
            {"message": {"total-results": len(items), "items": items}}
        )

    mock_api_client.request.side_effect = fake_request
    result = await works_client.batch_get(ids, batch_size=50)
    assert mock_api_client.request.await_count == 2
    assert len(result) == 60
    assert calls[0]["rows"] == 50
    assert calls[1]["rows"] == 10
    assert "10.1234/049" in calls[0]["filter"]
    assert "10.1234/059" in calls[1]["filter"]


@pytest.mark.asyncio
async def test_batch_get_no_results(works_client, mock_api_client):
    mock_api_client.request.return_value = _mock_response(
        {"message": {"total-results": 0, "items": []}}
    )
    result = await works_client.batch_get(["10.1234/missing"])
    assert result == {}


# ---------------------------------------------------------------------------
# Key normalization
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_batch_get_doi_normalizes_case_and_prefix(works_client, mock_api_client):
    """API returns lowercase bare DOIs; keys must be normalized the same way."""
    mock_api_client.request.return_value = _mock_response(
        {
            "message": {
                "total-results": 1,
                "items": [{"DOI": "https://doi.org/10.1234/alpha"}],
            }
        }
    )
    result = await works_client.batch_get(["10.1234/ALPHA"])
    assert "10.1234/alpha" in result


@pytest.mark.asyncio
async def test_batch_get_raw_fallback_resolves_uppercase_doi(
    works_client, mock_api_client
):
    """Raw response items still resolve Crossref's uppercase DOI key."""
    raw_work = {"DOI": "10.1234/raw", "issued": "not-a-date"}
    mock_api_client.request.return_value = _mock_response(
        {"message": {"total-results": 1, "items": [raw_work]}}
    )
    result = await works_client.batch_get(["10.1234/raw"])
    assert result == {"10.1234/raw": raw_work}


@pytest.mark.asyncio
async def test_batch_get_custom_field_and_key_fn(works_client, mock_api_client):
    """Custom field name and key function pass through correctly."""
    mock_api_client.request.return_value = _mock_response(
        {"message": {"total-results": 1, "items": [{"ISSN": ["1234-5678"]}]}}
    )
    result = await works_client.batch_get(
        ["1234-5678"], field="issn", key_fn=lambda e: e.issn[0]
    )
    assert _params(mock_api_client)["filter"] == "issn:1234-5678"
    assert "1234-5678" in result


# ---------------------------------------------------------------------------
# Auto-generated batch_get_by_doi
# ---------------------------------------------------------------------------


def test_works_client_has_batch_get_by_doi():
    assert hasattr(WorksClient, "batch_get_by_doi")


@pytest.mark.asyncio
async def test_batch_get_by_doi(works_client, mock_api_client):
    mock_api_client.request.return_value = _mock_response(RESULTS_A_B)
    result = await works_client.batch_get_by_doi(["10.1234/alpha", "10.5678/beta"])
    assert set(result) == {"10.1234/alpha", "10.5678/beta"}
    filter_str = _params(mock_api_client)["filter"]
    assert filter_str == "doi:10.1234/alpha,doi:10.5678/beta"
    assert "|" not in filter_str  # pipe-OR is not supported by Crossref
