"""Tests for WorksClient."""

import pytest

from stavrophora.models import ApiResponse, Work
from stavrophora.resources.works_client import WorksClient

from .conftest import _mock_response

# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

MINIMAL_WORK = {
    "DOI": "10.1234/w123",
    "title": ["A Test Paper"],
    "type": "journal-article",
}

SEARCH_RESPONSE = {
    "status": "ok",
    "message": {"total-results": 1, "items": [MINIMAL_WORK]},
}

EMPTY_SEARCH_RESPONSE = {"status": "ok", "message": {"total-results": 0, "items": []}}

PAGE1 = {
    "status": "ok",
    "message": {
        "total-results": 3,
        "next-cursor": "CURSOR_PAGE_2",
        "items": [{"DOI": "10.1234/a"}, {"DOI": "10.1234/b"}],
    },
}

PAGE2 = {
    "status": "ok",
    "message": {
        "total-results": 3,
        "next-cursor": "CURSOR_PAGE_3",  # last non-empty page still carries a cursor
        "items": [{"DOI": "10.1234/c"}],
    },
}

PAGE3_EMPTY = {"status": "ok", "message": {"total-results": 3, "items": []}}


@pytest.fixture
def works_client(mock_api_client):
    return WorksClient(mock_api_client)


def _params(mock_api_client, index=-1):
    return mock_api_client.request.call_args_list[index].kwargs["params"]


# ---------------------------------------------------------------------------
# get()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_work_encodes_doi(works_client, mock_api_client):
    mock_api_client.request.return_value = _mock_response({"message": MINIMAL_WORK})
    work = await works_client.get("10.1038/Nature12373")
    assert isinstance(work, Work)
    assert work.doi == "10.1234/w123"
    path = mock_api_client.request.call_args.args[1]
    assert path == "works/10.1038/nature12373"


@pytest.mark.asyncio
async def test_get_work_prefixes_stripped(works_client, mock_api_client):
    mock_api_client.request.return_value = _mock_response({"message": MINIMAL_WORK})
    await works_client.get("https://doi.org/10.1038/nature12373")
    path = mock_api_client.request.call_args.args[1]
    assert path == "works/10.1038/nature12373"


@pytest.mark.asyncio
async def test_get_work_raises_bibliofabric_error_on_404(works_client, mock_api_client):
    from bibliofabric.exceptions import BibliofabricError

    mock_api_client.request.side_effect = BibliofabricError("404")
    with pytest.raises(BibliofabricError):
        await works_client.get("10.9999/nonexistent")


# ---------------------------------------------------------------------------
# agency()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_agency(works_client, mock_api_client):
    mock_api_client.request.return_value = _mock_response(
        {
            "message": {
                "DOI": "10.1038/nature12373",
                "agency": {"id": "crossref", "label": "Crossref"},
            }
        }
    )
    result = await works_client.agency("10.1038/nature12373")
    assert result.agency.label == "Crossref"
    path = mock_api_client.request.call_args.args[1]
    assert path == "works/10.1038/nature12373/agency"


# ---------------------------------------------------------------------------
# search()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_works_no_filters(works_client, mock_api_client):
    mock_api_client.request.return_value = _mock_response(SEARCH_RESPONSE)
    result = await works_client.search()
    assert isinstance(result, ApiResponse)
    assert result.message.total_results == 1
    assert result.message.items[0].doi == "10.1234/w123"
    params = _params(mock_api_client)
    assert params["rows"] == 20
    assert params["offset"] == 0
    assert "page" not in params  # Crossref rejects a page parameter
    assert "filter" not in params


@pytest.mark.asyncio
async def test_search_works_offset_from_page(works_client, mock_api_client):
    mock_api_client.request.return_value = _mock_response(SEARCH_RESPONSE)
    await works_client.search(page=3, page_size=25)
    params = _params(mock_api_client)
    assert params["offset"] == 50
    assert params["rows"] == 25


@pytest.mark.asyncio
async def test_search_works_with_filters(works_client, mock_api_client):
    mock_api_client.request.return_value = _mock_response(SEARCH_RESPONSE)
    await works_client.search(filters={"type": "journal-article", "has-abstract": True})
    filter_str = _params(mock_api_client)["filter"]
    assert filter_str == "type:journal-article,has-abstract:true"


@pytest.mark.asyncio
async def test_search_works_list_filter_repeats_keys(works_client, mock_api_client):
    """List values become repeated key:value pairs (Crossref OR syntax)."""
    mock_api_client.request.return_value = _mock_response(SEARCH_RESPONSE)
    await works_client.search(
        filters={"doi": ["10.1038/a", "10.1038/b"]},
    )
    assert _params(mock_api_client)["filter"] == "doi:10.1038/a,doi:10.1038/b"


@pytest.mark.asyncio
async def test_search_works_with_filters_model(works_client, mock_api_client):
    from stavrophora.endpoints import WorksFilters

    mock_api_client.request.return_value = _mock_response(SEARCH_RESPONSE)
    await works_client.search(
        filters=WorksFilters(type="journal-article", from_pub_date="2026-01-01")
    )
    filter_str = _params(mock_api_client)["filter"]
    assert filter_str == "type:journal-article,from-pub-date:2026-01-01"


@pytest.mark.asyncio
async def test_search_sort_and_order(works_client, mock_api_client):
    """sort_by='field:desc' translates to sort=field&order=desc."""
    mock_api_client.request.return_value = _mock_response(SEARCH_RESPONSE)
    await works_client.search(sort_by="is-referenced-by-count:desc")
    params = _params(mock_api_client)
    assert params["sort"] == "is-referenced-by-count"
    assert params["order"] == "desc"


@pytest.mark.asyncio
async def test_search_sort_field_only(works_client, mock_api_client):
    mock_api_client.request.return_value = _mock_response(SEARCH_RESPONSE)
    await works_client.search(sort_by="score")
    params = _params(mock_api_client)
    assert params["sort"] == "score"
    assert "order" not in params


@pytest.mark.asyncio
async def test_search_select(works_client, mock_api_client):
    mock_api_client.request.return_value = _mock_response(SEARCH_RESPONSE)
    await works_client.search(select=["DOI", "title", "is-referenced-by-count"])
    assert _params(mock_api_client)["select"] == "DOI,title,is-referenced-by-count"


@pytest.mark.asyncio
async def test_search_query_param(works_client, mock_api_client):
    mock_api_client.request.return_value = _mock_response(SEARCH_RESPONSE)
    await works_client.search(search="climate adaptation")
    assert _params(mock_api_client)["query"] == "climate adaptation"


@pytest.mark.asyncio
async def test_search_parses_string_archive(works_client, mock_api_client):
    """Regression (live 2026-09): ``archive`` is a list of bare strings
    (["CLOCKSS", "LOCKSS", "Portico"]), not objects — the envelope must
    parse into ApiResponse[Work], not fall back to raw data."""
    mock_api_client.request.return_value = _mock_response(
        {
            "status": "ok",
            "message": {
                "total-results": 1,
                "items": [
                    {
                        "DOI": "10.7717/peerj.1",
                        "archive": ["CLOCKSS", "LOCKSS", "Portico"],
                    }
                ],
            },
        }
    )
    from stavrophora.models import ApiResponse, Work

    response = await works_client.search(page_size=1)
    assert isinstance(response, ApiResponse)
    work = response.message.items[0]
    assert isinstance(work, Work)
    assert work.archive == ["CLOCKSS", "LOCKSS", "Portico"]


@pytest.mark.asyncio
async def test_search_invalid_filters_rejected(works_client):
    from bibliofabric.exceptions import BibliofabricError

    with pytest.raises(BibliofabricError):
        await works_client.search(filters="type:journal-article")


@pytest.mark.asyncio
async def test_search_wraps_unexpected_error(works_client, mock_api_client):
    from bibliofabric.exceptions import BibliofabricError

    mock_api_client.request.side_effect = RuntimeError("boom")
    with pytest.raises(BibliofabricError, match="Unexpected error"):
        await works_client.search()


# ---------------------------------------------------------------------------
# iterate()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_iterate_works_follows_cursor(works_client, mock_api_client):
    """Cursor pages are followed; the final empty page terminates iteration."""
    mock_api_client.request.side_effect = [
        _mock_response(PAGE1),
        _mock_response(PAGE2),
        _mock_response(PAGE3_EMPTY),
    ]
    dois = [w.doi async for w in works_client.iterate(page_size=2)]
    assert dois == ["10.1234/a", "10.1234/b", "10.1234/c"]
    assert mock_api_client.request.await_count == 3
    first_params = mock_api_client.request.call_args_list[0].kwargs["params"]
    second_params = mock_api_client.request.call_args_list[1].kwargs["params"]
    assert first_params["cursor"] == "*"
    assert second_params["cursor"] == "CURSOR_PAGE_2"


@pytest.mark.asyncio
async def test_iterate_works_no_cursor_stops(works_client, mock_api_client):
    mock_api_client.request.return_value = _mock_response(EMPTY_SEARCH_RESPONSE)
    dois = [w.doi async for w in works_client.iterate(page_size=2)]
    assert dois == []
    assert mock_api_client.request.await_count == 1


@pytest.mark.asyncio
async def test_iterate_works_sort_split(works_client, mock_api_client):
    mock_api_client.request.side_effect = [
        _mock_response(PAGE1),
        _mock_response(PAGE3_EMPTY),
    ]
    async for _ in works_client.iterate(page_size=2, sort_by="indexed:asc"):
        pass
    params = mock_api_client.request.call_args_list[0].kwargs["params"]
    assert params["sort"] == "indexed"
    assert params["order"] == "asc"


@pytest.mark.asyncio
async def test_iterate_works_select(works_client, mock_api_client):
    mock_api_client.request.side_effect = [
        _mock_response(PAGE1),
        _mock_response(PAGE3_EMPTY),
    ]
    async for _ in works_client.iterate(page_size=2, select=["DOI"]):
        pass
    params = mock_api_client.request.call_args_list[0].kwargs["params"]
    assert params["select"] == "DOI"


# ---------------------------------------------------------------------------
# count()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_count_reads_total_results(works_client, mock_api_client):
    mock_api_client.request.return_value = _mock_response(SEARCH_RESPONSE)
    assert await works_client.count(filters={"type": "journal-article"}) == 1
    assert _params(mock_api_client)["rows"] == 1
