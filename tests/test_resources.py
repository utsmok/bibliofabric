# tests/test_resources.py
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from pydantic import BaseModel, Field

from bibliofabric.client import BaseApiClient
from bibliofabric.exceptions import BibliofabricError
from bibliofabric.models import ResponseUnwrapper
from bibliofabric.resources import (
    BaseResourceClient,
    CursorIterableMixin,
    GettableMixin,
    SearchableMixin,
)

# --- Mocks and Fixtures ---


class MockEntityModel(BaseModel):
    id: str
    value: str


class MockSearchResponseModel(BaseModel):
    results: list[MockEntityModel]
    total: int = Field(alias="numFound")  # Example alias


@pytest.fixture
def mock_api_client():
    client = AsyncMock(spec=BaseApiClient)
    client.request = AsyncMock()
    client._settings = MagicMock()  # Mock settings if BaseApiClient accesses it
    client._settings.cache_ttl = 300  # Example setting
    client._settings.cache_maxsize = 128  # Example setting
    return client


@pytest.fixture
def mock_unwrapper():
    unwrapper = AsyncMock(spec=ResponseUnwrapper)
    unwrapper.unwrap_results = MagicMock()
    unwrapper.unwrap_single_item = MagicMock()
    unwrapper.get_next_page_token = MagicMock()
    unwrapper.get_total_results = MagicMock()
    return unwrapper


class ConcreteResourceClient(BaseResourceClient):
    _entity_path = "test_entities"
    _entity_model = MockEntityModel
    _search_response_model = MockSearchResponseModel

    def __init__(self, api_client: BaseApiClient, unwrapper: ResponseUnwrapper):
        super().__init__(api_client=api_client)
        # Directly assign unwrapper for testing, bypassing property logic if needed
        self._unwrapper_instance = unwrapper

    @property
    def response_unwrapper(self) -> ResponseUnwrapper:  # type: ignore[override]
        return self._unwrapper_instance


class GettableTestClient(GettableMixin, ConcreteResourceClient):
    pass


class SearchableTestClient(SearchableMixin, ConcreteResourceClient):
    pass


class CursorIterableTestClient(CursorIterableMixin, ConcreteResourceClient):
    pass


@pytest.fixture
def gettable_client(mock_api_client, mock_unwrapper):
    return GettableTestClient(mock_api_client, mock_unwrapper)


@pytest.fixture
def searchable_client(mock_api_client, mock_unwrapper):
    return SearchableTestClient(mock_api_client, mock_unwrapper)


@pytest.fixture
def cursor_iterable_client(mock_api_client, mock_unwrapper):
    return CursorIterableTestClient(mock_api_client, mock_unwrapper)


# --- BaseResourceClient Tests ---


def test_base_resource_client_init(mock_api_client, mock_unwrapper):
    client = ConcreteResourceClient(mock_api_client, mock_unwrapper)
    assert client._api_client == mock_api_client
    assert client.response_unwrapper == mock_unwrapper


# --- GettableMixin Tests ---


@pytest.mark.asyncio
async def test_gettable_mixin_get_success(
    gettable_client, mock_api_client, mock_unwrapper
):
    entity_id = "123"
    mock_raw_item = {"id": entity_id, "value": "Test Value"}

    # Mock the response from BaseApiClient.request
    mock_response = MagicMock(
        spec=httpx.Response
    )  # Ensure it's a spec for httpx.Response
    mock_response.json.return_value = {
        "results": [mock_raw_item],
        "header": {"numFound": 1},
    }
    mock_api_client.request.return_value = (
        mock_response  # Should return the response object directly
    )

    # Mock the unwrapper's behavior
    mock_unwrapper.unwrap_results.return_value = [mock_raw_item]

    result = await gettable_client.get(entity_id)

    mock_api_client.request.assert_awaited_once_with(
        "GET", "test_entities", params={"id": entity_id, "pageSize": 1}
    )
    mock_unwrapper.unwrap_results.assert_called_once_with(
        {"results": [mock_raw_item], "header": {"numFound": 1}}
    )
    assert isinstance(result, MockEntityModel)
    assert result.id == entity_id
    assert result.value == "Test Value"


@pytest.mark.asyncio
async def test_gettable_mixin_get_not_found(
    gettable_client, mock_api_client, mock_unwrapper
):
    entity_id = "notfound"
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = {
        "results": [],
        "header": {"numFound": 0},
    }  # Empty results
    mock_api_client.request.return_value = mock_response
    mock_unwrapper.unwrap_results.return_value = []

    with pytest.raises(
        BibliofabricError, match=f"MockEntityModel with ID '{entity_id}' not found."
    ):
        await gettable_client.get(entity_id)


@pytest.mark.asyncio
async def test_gettable_mixin_get_no_entity_model(
    gettable_client, mock_api_client, mock_unwrapper
):
    entity_id = "raw123"
    mock_raw_item = {"id": entity_id, "value": "Raw Value"}
    gettable_client._entity_model = None  # type: ignore[assignment]

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = {"results": [mock_raw_item]}
    mock_api_client.request.return_value = mock_response
    mock_unwrapper.unwrap_results.return_value = [mock_raw_item]

    result = await gettable_client.get(entity_id)
    assert result == mock_raw_item  # Should return raw dict


@pytest.mark.asyncio
async def test_gettable_mixin_get_parsing_error(
    gettable_client, mock_api_client, mock_unwrapper
):
    entity_id = "parse_error"
    # Data that will cause a Pydantic validation error (e.g., missing 'value')
    mock_raw_item_invalid = {"id": entity_id}

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = {"results": [mock_raw_item_invalid]}
    mock_api_client.request.return_value = mock_response
    mock_unwrapper.unwrap_results.return_value = [mock_raw_item_invalid]

    # Should log a warning and return raw data
    result = await gettable_client.get(entity_id)
    assert result == mock_raw_item_invalid


# --- SearchableMixin Tests ---


@pytest.mark.asyncio
async def test_searchable_mixin_search_success(
    searchable_client, mock_api_client, mock_unwrapper
):
    mock_raw_results = [{"id": "1", "value": "A"}, {"id": "2", "value": "B"}]
    mock_response_json = {"results": mock_raw_results, "numFound": 2}

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = mock_response_json
    mock_api_client.request.return_value = mock_response  # response

    filters = {"custom_filter": "test"}
    result = await searchable_client.search(
        page=1, page_size=10, sort_by="id asc", filters=filters
    )

    expected_params = {
        "page": 1,
        "pageSize": 10,
        "sortBy": "id asc",
        "custom_filter": "test",
    }
    mock_api_client.request.assert_awaited_once_with(
        "GET", "test_entities", params=expected_params
    )
    assert isinstance(result, MockSearchResponseModel)
    assert len(result.results) == 2
    assert result.results[0].id == "1"
    assert result.total == 2


@pytest.mark.asyncio
async def test_searchable_mixin_search_no_search_model(
    searchable_client, mock_api_client
):
    searchable_client._search_response_model = None  # type: ignore[assignment]
    mock_raw_response_json = {"results": [{"id": "1", "value": "A"}]}

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = mock_raw_response_json
    mock_api_client.request.return_value = mock_response

    result = await searchable_client.search()
    assert result == mock_raw_response_json


@pytest.mark.asyncio
async def test_searchable_mixin_search_parsing_error(
    searchable_client, mock_api_client
):
    # Response that will fail MockSearchResponseModel validation (e.g. 'results' is not a list)
    mock_invalid_response_json = {"results": "not_a_list", "numFound": 0}

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = mock_invalid_response_json
    mock_api_client.request.return_value = mock_response

    # Should log warning and return raw data
    result = await searchable_client.search()
    assert result == mock_invalid_response_json


# --- CursorIterableMixin Tests ---


@pytest.mark.asyncio
async def test_cursor_iterable_mixin_iterate_success(
    cursor_iterable_client, mock_api_client, mock_unwrapper
):
    page1_items = [{"id": "1", "value": "Val1"}]
    page2_items = [{"id": "2", "value": "Val2"}]

    # Mock API responses for two pages
    response1_json = {"results": page1_items, "header": {"nextCursor": "cursor2"}}
    response2_json = {"results": page2_items, "header": {"nextCursor": None}}

    mock_response1 = MagicMock(spec=httpx.Response)
    mock_response1.json.return_value = response1_json
    mock_response2 = MagicMock(spec=httpx.Response)
    mock_response2.json.return_value = response2_json

    mock_api_client.request.side_effect = [mock_response1, mock_response2]

    # Mock unwrapper behavior
    mock_unwrapper.unwrap_results.side_effect = [page1_items, page2_items]
    mock_unwrapper.get_next_page_token.side_effect = ["cursor2", None]

    results = []
    async for item in cursor_iterable_client.iterate(
        page_size=1, filters={"active": True}
    ):
        results.append(item)

    assert len(results) == 2
    assert isinstance(results[0], MockEntityModel)
    assert results[0].id == "1"
    assert isinstance(results[1], MockEntityModel)
    assert results[1].id == "2"

    calls = mock_api_client.request.call_args_list
    assert len(calls) == 2

    args, kwargs = calls[0]
    assert args == ("GET", "test_entities")
    assert kwargs == {"params": {"cursor": "*", "pageSize": 1, "active": True}}

    args, kwargs = calls[1]
    assert args == ("GET", "test_entities")
    assert kwargs == {"params": {"cursor": "cursor2", "pageSize": 1, "active": True}}

    assert mock_unwrapper.unwrap_results.call_count == 2
    assert mock_unwrapper.get_next_page_token.call_count == 2


@pytest.mark.asyncio
async def test_cursor_iterable_mixin_iterate_no_entity_model(
    cursor_iterable_client, mock_api_client, mock_unwrapper
):
    cursor_iterable_client._entity_model = None  # type: ignore[assignment]
    page1_items_raw = [{"id": "raw1", "value": "RawVal1"}]

    response1_json = {"results": page1_items_raw, "header": {"nextCursor": None}}
    mock_response1 = MagicMock(spec=httpx.Response)
    mock_response1.json.return_value = response1_json
    mock_api_client.request.return_value = mock_response1

    mock_unwrapper.unwrap_results.return_value = page1_items_raw
    mock_unwrapper.get_next_page_token.return_value = None

    results = [item async for item in cursor_iterable_client.iterate()]


    assert len(results) == 1
    assert results[0] == page1_items_raw[0]  # Should be raw dict


@pytest.mark.asyncio
async def test_cursor_iterable_mixin_iterate_parsing_error(
    cursor_iterable_client, mock_api_client, mock_unwrapper
):
    # Data that will cause validation error
    page1_items_invalid = [{"id": "invalid_item"}]

    response1_json = {"results": page1_items_invalid, "header": {"nextCursor": None}}
    mock_response1 = MagicMock(spec=httpx.Response)
    mock_response1.json.return_value = response1_json
    mock_api_client.request.return_value = mock_response1

    mock_unwrapper.unwrap_results.return_value = page1_items_invalid
    mock_unwrapper.get_next_page_token.return_value = None

    results = [item async for item in cursor_iterable_client.iterate()]


    assert len(results) == 1
    assert results[0] == page1_items_invalid[0]


@pytest.mark.asyncio
async def test_cursor_iterable_mixin_iterate_empty_initial_results(
    cursor_iterable_client, mock_api_client, mock_unwrapper
):
    response_json = {"results": [], "header": {"nextCursor": None}}
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = response_json
    mock_api_client.request.return_value = mock_response

    mock_unwrapper.unwrap_results.return_value = []
    mock_unwrapper.get_next_page_token.return_value = None


    results = [item async for item in cursor_iterable_client.iterate()]

    assert len(results) == 0
    mock_api_client.request.assert_awaited_once()  # Should make one call
    mock_unwrapper.unwrap_results.assert_called_once()
    mock_unwrapper.get_next_page_token.assert_called_once()  # Still checks for next token
