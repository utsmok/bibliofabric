"""Additional tests for resources.py to cover pagination edge cases, sort validation, and filter conversion."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel, Field

from bibliofabric.client import BaseApiClient
from bibliofabric.exceptions import BibliofabricError
from bibliofabric.models import ResponseUnwrapper
from bibliofabric.resources import (
    BaseResourceClient,
    CursorIterableMixin,
    GettableMixin,
    PageIterableMixin,
    SearchableMixin,
)


class MockEntityModel(BaseModel):
    id: str
    value: str


class MockSearchResponseModel(BaseModel):
    results: list[MockEntityModel]
    total: int = Field(alias="numFound")


EXPECTED_TWO_ITEMS = 2


class SampleFilter(BaseModel):
    model_config = {"populate_by_name": True}
    search_term: str = Field(alias="searchTerm")
    category: str | None = None


@pytest.fixture
def mock_api_client():
    client = AsyncMock(spec=BaseApiClient)
    client._response_unwrapper = MagicMock(spec=ResponseUnwrapper)
    return client


@pytest.fixture
def mock_unwrapper():
    return MagicMock(spec=ResponseUnwrapper)


class ConcreteResourceClient(BaseResourceClient):
    _entity_path = "test_entities"
    _entity_model = MockEntityModel
    _search_response_model = MockSearchResponseModel

    def __init__(self, api_client, unwrapper_instance, **kwargs):
        super().__init__(api_client, **kwargs)
        self._unwrapper_instance = unwrapper_instance

    @property
    def response_unwrapper(self):
        return self._unwrapper_instance


# --- GettableMixin edge cases ---


class GettableNoPathClient(GettableMixin, ConcreteResourceClient):
    _entity_path = ""


class GettableDirectGetClient(GettableMixin, ConcreteResourceClient):
    _entity_path = "entities"
    _supports_direct_get = True
    _entity_model = MockEntityModel


@pytest.mark.asyncio
async def test_gettable_no_entity_path_raises(mock_api_client, mock_unwrapper):
    """Test that get() raises when _entity_path is empty (line 140)."""
    client = GettableNoPathClient(mock_api_client, mock_unwrapper)
    with pytest.raises(BibliofabricError, match="must define _entity_path"):
        await client.get("123")


@pytest.mark.asyncio
async def test_gettable_direct_get_model_parse_fallback(
    mock_api_client, mock_unwrapper
):
    """Test direct get with model parsing failure returns raw data (lines 183-188)."""
    client = GettableDirectGetClient(mock_api_client, mock_unwrapper)

    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "123", "wrong_field": "data"}
    mock_api_client.request = AsyncMock(return_value=mock_response)
    mock_unwrapper.unwrap_single_item.return_value = {
        "id": "123",
        "wrong_field": "data",
    }

    result = await client.get("123")
    assert isinstance(result, dict)
    assert result["id"] == "123"


@pytest.mark.asyncio
async def test_gettable_unexpected_error_wraps(mock_api_client, mock_unwrapper):
    """Test that unexpected errors in get() are wrapped (lines 194-199)."""
    client = GettableDirectGetClient(mock_api_client, mock_unwrapper)
    mock_api_client.request = AsyncMock(side_effect=ValueError("unexpected"))

    with pytest.raises(BibliofabricError, match="Unexpected error fetching entity"):
        await client.get("123")


# --- SearchableMixin edge cases ---


class SearchableNoPathClient(SearchableMixin, ConcreteResourceClient):
    _entity_path = ""


class SearchableTestClient(SearchableMixin, ConcreteResourceClient):
    _entity_path = "test"


@pytest.mark.asyncio
async def test_searchable_no_entity_path_raises(mock_api_client, mock_unwrapper):
    """Test that search() raises when _entity_path is empty (line 246)."""
    client = SearchableNoPathClient(mock_api_client, mock_unwrapper)
    with pytest.raises(BibliofabricError, match="must define _entity_path"):
        await client.search()


@pytest.mark.asyncio
async def test_searchable_invalid_filter_type_raises(mock_api_client, mock_unwrapper):
    """Test that search() raises when filters is invalid type (line 258)."""
    client = SearchableTestClient(mock_api_client, mock_unwrapper)
    with pytest.raises(
        BibliofabricError, match="filters must be a Pydantic model or dictionary"
    ):
        await client.search(filters="invalid")  # type: ignore


@pytest.mark.asyncio
async def test_searchable_unexpected_error_wraps(mock_api_client, mock_unwrapper):
    """Test that unexpected errors in search() are wrapped (lines 293-299)."""
    client = SearchableTestClient(mock_api_client, mock_unwrapper)
    mock_api_client.request = AsyncMock(side_effect=ValueError("unexpected"))

    with pytest.raises(BibliofabricError, match="Unexpected error searching"):
        await client.search()


@pytest.mark.asyncio
async def test_searchable_bibliofabric_error_reraise(mock_api_client, mock_unwrapper):
    """Test that BibliofabricError from request() is re-raised as-is (line 295)."""
    client = SearchableTestClient(mock_api_client, mock_unwrapper)
    mock_api_client.request = AsyncMock(side_effect=BibliofabricError("original error"))

    with pytest.raises(BibliofabricError, match="original error"):
        await client.search()


@pytest.mark.asyncio
async def test_searchable_pydantic_filter_conversion(mock_api_client, mock_unwrapper):
    """Test that Pydantic model filters are properly converted (line 254)."""
    client = SearchableTestClient(mock_api_client, mock_unwrapper)

    mock_response = MagicMock()
    mock_response.json.return_value = {"results": [], "numFound": 0}
    mock_api_client.request = AsyncMock(return_value=mock_response)

    filter_model = SampleFilter(search_term="test")
    await client.search(filters=filter_model)

    call_args = mock_api_client.request.call_args
    params = call_args[1]["params"]
    assert "searchTerm" in params
    assert params["searchTerm"] == "test"


# --- CursorIterableMixin edge cases ---


class CursorIterableNoPathClient(CursorIterableMixin, ConcreteResourceClient):
    _entity_path = ""


class CursorIterableTestClient(CursorIterableMixin, ConcreteResourceClient):
    _entity_path = "test_entities"


@pytest.mark.asyncio
async def test_cursor_iterable_no_entity_path_raises(mock_api_client, mock_unwrapper):
    """Test that iterate() raises when _entity_path is empty (line 346)."""
    client = CursorIterableNoPathClient(mock_api_client, mock_unwrapper)
    with pytest.raises(BibliofabricError, match="must define _entity_path"):
        async for _ in client.iterate():
            pass


@pytest.mark.asyncio
async def test_cursor_iterable_invalid_filter_type_raises(
    mock_api_client, mock_unwrapper
):
    """Test that iterate() raises when filters is invalid type (line 358)."""
    client = CursorIterableTestClient(mock_api_client, mock_unwrapper)
    with pytest.raises(
        BibliofabricError, match="filters must be a Pydantic model or dictionary"
    ):
        async for _ in client.iterate(filters="invalid"):  # type: ignore
            pass


@pytest.mark.asyncio
async def test_cursor_iterable_with_sort(mock_api_client, mock_unwrapper):
    """Test that sort_by is passed as parameter (line 376)."""
    client = CursorIterableTestClient(mock_api_client, mock_unwrapper)

    mock_response = MagicMock()
    mock_response.json.return_value = {"results": [], "header": {}}
    mock_api_client.request = AsyncMock(return_value=mock_response)
    mock_unwrapper.unwrap_results.return_value = []
    mock_unwrapper.get_next_page_token.return_value = None

    async for _ in client.iterate(sort_by="title asc"):
        pass

    call_args = mock_api_client.request.call_args
    assert call_args[1]["params"]["sortBy"] == "title ASC"


@pytest.mark.asyncio
async def test_cursor_iterable_unexpected_error_wraps(mock_api_client, mock_unwrapper):
    """Test that unexpected errors during iteration are wrapped (lines 434-440)."""
    client = CursorIterableTestClient(mock_api_client, mock_unwrapper)
    mock_api_client.request = AsyncMock(side_effect=ValueError("unexpected"))

    with pytest.raises(BibliofabricError, match="Unexpected error during iteration"):
        async for _ in client.iterate():
            pass


@pytest.mark.asyncio
async def test_cursor_iterable_bibliofabric_error_reraise(
    mock_api_client, mock_unwrapper
):
    """Test that BibliofabricError during iteration is re-raised as-is (line 436)."""
    client = CursorIterableTestClient(mock_api_client, mock_unwrapper)
    mock_api_client.request = AsyncMock(side_effect=BibliofabricError("original error"))

    with pytest.raises(BibliofabricError, match="original error"):
        async for _ in client.iterate():
            pass


@pytest.mark.asyncio
async def test_cursor_iterable_pydantic_filter_conversion(
    mock_api_client, mock_unwrapper
):
    """Test that Pydantic model filters are properly converted in cursor iterable (line 354)."""
    client = CursorIterableTestClient(mock_api_client, mock_unwrapper)

    mock_response = MagicMock()
    mock_response.json.return_value = {"results": [], "header": {}}
    mock_api_client.request = AsyncMock(return_value=mock_response)
    mock_unwrapper.unwrap_results.return_value = []
    mock_unwrapper.get_next_page_token.return_value = None

    filter_model = SampleFilter(search_term="test")
    async for _ in client.iterate(filters=filter_model):
        pass

    call_args = mock_api_client.request.call_args
    params = call_args[1]["params"]
    assert "searchTerm" in params


# --- PageIterableMixin edge cases ---


class PageIterableNoPathClient(PageIterableMixin, ConcreteResourceClient):
    _entity_path = ""


class PageIterableTestClient(PageIterableMixin, ConcreteResourceClient):
    _entity_path = "test_entities"


@pytest.mark.asyncio
async def test_page_iterable_no_entity_path_raises(mock_api_client, mock_unwrapper):
    """Test that iterate() raises when _entity_path is empty (line 482)."""
    client = PageIterableNoPathClient(mock_api_client, mock_unwrapper)
    with pytest.raises(BibliofabricError, match="must define _entity_path"):
        async for _ in client.iterate():
            pass


@pytest.mark.asyncio
async def test_page_iterable_invalid_filter_type_raises(
    mock_api_client, mock_unwrapper
):
    """Test that iterate() raises when filters is invalid type (lines 489-494)."""
    client = PageIterableTestClient(mock_api_client, mock_unwrapper)
    with pytest.raises(
        BibliofabricError, match="filters must be a Pydantic model or dictionary"
    ):
        async for _ in client.iterate(filters=12345):  # type: ignore
            pass


@pytest.mark.asyncio
async def test_page_iterable_with_sort_and_validation(mock_api_client, mock_unwrapper):
    """Test that sort_by passes through _validate_sort_field (lines 499-500)."""
    client = PageIterableTestClient(mock_api_client, mock_unwrapper)

    mock_response = MagicMock()
    mock_response.json.return_value = {"results": []}
    mock_api_client.request = AsyncMock(return_value=mock_response)
    mock_unwrapper.unwrap_results.return_value = []

    async for _ in client.iterate(sort_by="title desc"):
        pass

    call_args = mock_api_client.request.call_args
    assert call_args[1]["params"]["sortBy"] == "title DESC"


@pytest.mark.asyncio
async def test_page_iterable_no_entity_model_yields_raw(
    mock_api_client, mock_unwrapper
):
    """Test iteration without entity model yields raw dicts (lines 541-548)."""
    client = PageIterableTestClient(mock_api_client, mock_unwrapper)
    client._entity_model = None

    page1_data = [{"id": "1", "value": "a"}, {"id": "2", "value": "b"}]
    mock_response = MagicMock()
    mock_response.json.return_value = {"results": page1_data, "total": 2}
    mock_api_client.request = AsyncMock(return_value=mock_response)
    mock_unwrapper.unwrap_results.return_value = page1_data
    mock_unwrapper.get_total_results.return_value = EXPECTED_TWO_ITEMS

    results = [item async for item in client.iterate()]
    assert len(results) == EXPECTED_TWO_ITEMS
    assert results[0] == {"id": "1", "value": "a"}


@pytest.mark.asyncio
async def test_page_iterable_parsing_error_yields_raw(mock_api_client, mock_unwrapper):
    """Test that model parsing failure falls back to raw data (lines 541-548)."""
    client = PageIterableTestClient(mock_api_client, mock_unwrapper)

    page1_data = [{"id": "1"}]
    mock_response = MagicMock()
    mock_response.json.return_value = {"results": page1_data, "total": 1}
    mock_api_client.request = AsyncMock(return_value=mock_response)
    mock_unwrapper.unwrap_results.return_value = page1_data
    mock_unwrapper.get_total_results.return_value = 1

    results = [item async for item in client.iterate()]
    assert len(results) == 1
    assert results[0] == {"id": "1"}


@pytest.mark.asyncio
async def test_page_iterable_unexpected_error_wraps(mock_api_client, mock_unwrapper):
    """Test that unexpected errors during page iteration are wrapped (lines 562-568)."""
    client = PageIterableTestClient(mock_api_client, mock_unwrapper)
    mock_api_client.request = AsyncMock(side_effect=ValueError("unexpected"))

    with pytest.raises(BibliofabricError, match="Unexpected error during iteration"):
        async for _ in client.iterate():
            pass


@pytest.mark.asyncio
async def test_page_iterable_bibliofabric_error_reraise(
    mock_api_client, mock_unwrapper
):
    """Test that BibliofabricError during page iteration is re-raised as-is (line 564)."""
    client = PageIterableTestClient(mock_api_client, mock_unwrapper)
    mock_api_client.request = AsyncMock(side_effect=BibliofabricError("original error"))

    with pytest.raises(BibliofabricError, match="original error"):
        async for _ in client.iterate():
            pass


@pytest.mark.asyncio
async def test_page_iterable_pydantic_filter_conversion(
    mock_api_client, mock_unwrapper
):
    """Test that Pydantic model filters are properly converted in page iterable (line 490)."""
    client = PageIterableTestClient(mock_api_client, mock_unwrapper)

    mock_response = MagicMock()
    mock_response.json.return_value = {"results": []}
    mock_api_client.request = AsyncMock(return_value=mock_response)
    mock_unwrapper.unwrap_results.return_value = []

    filter_model = SampleFilter(search_term="test")
    async for _ in client.iterate(filters=filter_model):
        pass

    call_args = mock_api_client.request.call_args
    params = call_args[1]["params"]
    assert "searchTerm" in params


@pytest.mark.asyncio
async def test_page_iterable_dict_filter_conversion(mock_api_client, mock_unwrapper):
    """Test that dict filters are properly converted in page iterable (line 492)."""
    client = PageIterableTestClient(mock_api_client, mock_unwrapper)

    mock_response = MagicMock()
    mock_response.json.return_value = {"results": []}
    mock_api_client.request = AsyncMock(return_value=mock_response)
    mock_unwrapper.unwrap_results.return_value = []

    async for _ in client.iterate(filters={"key": "value"}):
        pass

    call_args = mock_api_client.request.call_args
    params = call_args[1]["params"]
    assert params["key"] == "value"
