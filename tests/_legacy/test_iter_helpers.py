# tests/test_iter_helpers.py
from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel

from bibliofabric.resources import BaseResourceClient, SearchableMixin


class FakeClient(SearchableMixin, BaseResourceClient):
    _entity_path = "test"
    _entity_model = None
    _search_response_model = None


class FakeHeader(BaseModel):
    numFound: int | None = None


class FakeResponse(BaseModel):
    header: FakeHeader = FakeHeader()
    results: list = []


@pytest.fixture
def mock_api():
    api = AsyncMock()
    return api


@pytest.fixture
def client(mock_api):
    return FakeClient(api_client=mock_api)


@pytest.mark.asyncio
async def test_collect_with_iterate(client, mock_api):
    """collect() should use iterate() if available."""

    # Add a mock iterate method
    async def fake_iterate(*, page_size=100, sort_by=None, filters=None):
        for i in range(5):
            yield {"id": i}

    client.iterate = fake_iterate

    results = await client.collect(limit=3)
    assert len(results) == 3
    assert results[0] == {"id": 0}


@pytest.mark.asyncio
async def test_collect_with_search_fallback(client, mock_api):
    """collect() should fall back to search() if iterate() unavailable."""
    resp = FakeResponse(header=FakeHeader(numFound=2), results=[{"id": 1}, {"id": 2}])
    client.search = AsyncMock(return_value=resp)
    results = await client.collect()
    assert len(results) == 2


@pytest.mark.asyncio
async def test_count(client, mock_api):
    """count() should return numFound from header."""
    resp = FakeResponse(header=FakeHeader(numFound=42), results=[])
    client.search = AsyncMock(return_value=resp)
    total = await client.count()
    assert total == 42


@pytest.mark.asyncio
async def test_count_dict_response(client, mock_api):
    """count() should handle raw dict response."""
    client.search = AsyncMock(return_value={"header": {"numFound": 99}, "results": []})
    total = await client.count()
    assert total == 99


@pytest.mark.asyncio
async def test_count_no_numfound(client, mock_api):
    """count() returns 0 when numFound is missing."""
    client.search = AsyncMock(return_value=FakeResponse())
    total = await client.count()
    assert total == 0


@pytest.mark.asyncio
async def test_first(client, mock_api):
    """first() should return the first result or None."""

    async def fake_iterate(*, page_size=100, sort_by=None, filters=None):
        yield {"id": 1}
        yield {"id": 2}

    client.iterate = fake_iterate

    result = await client.first()
    assert result == {"id": 1}


@pytest.mark.asyncio
async def test_first_empty(client, mock_api):
    """first() returns None when no results."""

    async def fake_iterate(*, page_size=100, sort_by=None, filters=None):
        return
        yield  # make it an async generator

    client.iterate = fake_iterate

    result = await client.first()
    assert result is None
