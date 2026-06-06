# tests/test_resources.py
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from pydantic import BaseModel, Field

from bibliofabric.client import BaseApiClient
from bibliofabric.exceptions import BibliofabricError, ValidationError
from bibliofabric.models import ResponseUnwrapper
from bibliofabric.resources import (
    BaseResourceClient,
    CursorIterableMixin,
    GettableMixin,
    PageIterableMixin,
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


class PageIterableTestClient(PageIterableMixin, ConcreteResourceClient):
    pass


class ValidatingSearchableClient(SearchableMixin, ConcreteResourceClient):
    _valid_sort_fields = frozenset({"title", "date"})

    def _validate_sort_field(self, field: str) -> None:
        if field not in self._valid_sort_fields:
            raise ValidationError(f"Invalid sort field: {field}")


class DirectGetTestClient(GettableMixin, ConcreteResourceClient):
    _supports_direct_get = True


@pytest.fixture
def gettable_client(mock_api_client, mock_unwrapper):
    return GettableTestClient(mock_api_client, mock_unwrapper)


@pytest.fixture
def searchable_client(mock_api_client, mock_unwrapper):
    return SearchableTestClient(mock_api_client, mock_unwrapper)


@pytest.fixture
def cursor_iterable_client(mock_api_client, mock_unwrapper):
    return CursorIterableTestClient(mock_api_client, mock_unwrapper)


@pytest.fixture
def page_iterable_client(mock_api_client, mock_unwrapper):
    return PageIterableTestClient(mock_api_client, mock_unwrapper)


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
        "GET",
        "test_entities",
        params={"id": entity_id, "pageSize": 1},
        base_url_override=None,
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
        "GET",
        "test_entities",
        params=expected_params,
        base_url_override=None,
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
    assert kwargs == {
        "params": {"cursor": "*", "pageSize": 1, "active": True},
        "base_url_override": None,
    }

    args, kwargs = calls[1]
    assert args == ("GET", "test_entities")
    assert kwargs == {
        "params": {"cursor": "cursor2", "pageSize": 1, "active": True},
        "base_url_override": None,
    }

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


# --- _base_url_override Tests ---


@pytest.mark.asyncio
async def test_searchable_mixin_base_url_override_passed(
    mock_api_client, mock_unwrapper
):
    """Test that _base_url_override is passed through to request()."""
    mock_raw_response_json = {"results": [], "numFound": 0}
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = mock_raw_response_json
    mock_api_client.request.return_value = mock_response

    client = SearchableTestClient(mock_api_client, mock_unwrapper)
    client._base_url_override = "https://custom.api.com/v1"

    await client.search()

    mock_api_client.request.assert_awaited_once()
    _, kwargs = mock_api_client.request.call_args
    assert kwargs.get("base_url_override") == "https://custom.api.com/v1"


@pytest.mark.asyncio
async def test_searchable_mixin_base_url_override_default_none(
    mock_api_client, mock_unwrapper
):
    """Test that default _base_url_override=None is passed through to request()."""
    mock_raw_response_json = {"results": [], "numFound": 0}
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = mock_raw_response_json
    mock_api_client.request.return_value = mock_response

    client = SearchableTestClient(mock_api_client, mock_unwrapper)
    # _base_url_override defaults to None

    await client.search()

    mock_api_client.request.assert_awaited_once()
    _, kwargs = mock_api_client.request.call_args
    assert kwargs.get("base_url_override") is None


# --- _validate_sort_field Tests ---


@pytest.mark.asyncio
async def test_validate_sort_field_raises_on_invalid(mock_api_client, mock_unwrapper):
    """Test that _validate_sort_field raises ValidationError for invalid sort fields."""
    client = ValidatingSearchableClient(mock_api_client, mock_unwrapper)

    with pytest.raises(ValidationError, match="Invalid sort field"):
        await client.search(sort_by="invalid_field asc")


@pytest.mark.asyncio
async def test_validate_sort_field_default_allows_any(mock_api_client, mock_unwrapper):
    """Test that default _validate_sort_field (no-op) allows any sort field."""
    mock_raw_response_json = {"results": [], "numFound": 0}
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = mock_raw_response_json
    mock_api_client.request.return_value = mock_response

    client = SearchableTestClient(mock_api_client, mock_unwrapper)
    client._search_response_model = None  # Return raw dict for easy assertion
    # Default _validate_sort_field is a no-op, should not raise
    result = await client.search(sort_by="any_field asc")

    assert result == mock_raw_response_json


# --- _supports_direct_get Tests ---


@pytest.mark.asyncio
async def test_gettable_mixin_direct_get_uses_path(mock_api_client, mock_unwrapper):
    """Test that _supports_direct_get=True uses direct path GET /{path}/{id}."""
    entity_id = "123"
    mock_raw_item = {"id": entity_id, "value": "Direct Value"}
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = mock_raw_item
    mock_api_client.request.return_value = mock_response
    mock_unwrapper.unwrap_single_item.return_value = mock_raw_item

    client = DirectGetTestClient(mock_api_client, mock_unwrapper)
    result = await client.get(entity_id)

    mock_api_client.request.assert_awaited_once()
    call_args, call_kwargs = mock_api_client.request.call_args
    assert call_args[1] == "test_entities/123"  # path should be direct
    assert call_kwargs.get("params") is None or "id" not in (
        call_kwargs.get("params") or {}
    )
    mock_unwrapper.unwrap_single_item.assert_called_once()


@pytest.mark.asyncio
async def test_gettable_mixin_default_uses_search_by_id(
    gettable_client, mock_api_client, mock_unwrapper
):
    """Test that default _supports_direct_get=False uses search-by-ID pattern."""
    entity_id = "123"
    mock_raw_item = {"id": entity_id, "value": "Test Value"}
    mock_raw_response_json = {"results": [mock_raw_item], "numFound": 1}
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = mock_raw_response_json
    mock_api_client.request.return_value = mock_response
    mock_unwrapper.unwrap_results.return_value = [mock_raw_item]

    result = await gettable_client.get(entity_id)

    mock_api_client.request.assert_awaited_once()
    _, kwargs = mock_api_client.request.call_args
    params = kwargs.get("params", {})
    assert params.get("id") == "123"
    assert params.get("pageSize") == 1
    mock_unwrapper.unwrap_results.assert_called_once()


# --- PageIterableMixin Tests ---


@pytest.mark.asyncio
async def test_page_iterable_mixin_basic_iteration(mock_api_client, mock_unwrapper):
    """Test that PageIterableMixin iterates pages 1, 2 and stops on empty page 3."""
    page1_items = [{"id": "1", "value": "A"}, {"id": "2", "value": "B"}]
    page2_items = [{"id": "3", "value": "C"}]

    responses = []
    for items in [page1_items, page2_items, []]:
        resp = MagicMock(spec=httpx.Response)
        resp.json.return_value = {"results": items}
        responses.append(resp)

    mock_api_client.request.side_effect = responses
    mock_unwrapper.unwrap_results.side_effect = [page1_items, page2_items, []]
    mock_unwrapper.get_total_results.return_value = None  # No total info

    client = PageIterableTestClient(mock_api_client, mock_unwrapper)
    results = [item async for item in client.iterate()]

    assert len(results) == 3
    assert results[0].id == "1"
    assert results[1].id == "2"
    assert results[2].id == "3"
    assert mock_api_client.request.await_count == 3


@pytest.mark.asyncio
async def test_page_iterable_mixin_stops_on_total(mock_api_client, mock_unwrapper):
    """Test that PageIterableMixin stops early when total results are reached."""
    page1_items = [{"id": "1", "value": "A"}, {"id": "2", "value": "B"}]
    page2_items = [{"id": "3", "value": "C"}]

    responses = []
    for items in [page1_items, page2_items]:
        resp = MagicMock(spec=httpx.Response)
        resp.json.return_value = {"results": items}
        responses.append(resp)

    mock_api_client.request.side_effect = responses
    mock_unwrapper.unwrap_results.side_effect = [page1_items, page2_items]
    # Total is 3, page_size=2: after page 2 (fetched=4>=3), iteration stops
    mock_unwrapper.get_total_results.return_value = 3

    client = PageIterableTestClient(mock_api_client, mock_unwrapper)
    results = [item async for item in client.iterate(page_size=2)]

    assert len(results) == 3
    assert mock_api_client.request.await_count == 2  # Stopped after 2 pages


@pytest.mark.asyncio
async def test_page_iterable_mixin_base_url_override(mock_api_client, mock_unwrapper):
    """Test that _base_url_override is passed through in PageIterableMixin requests."""
    response_json = {"results": []}
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = response_json
    mock_api_client.request.return_value = mock_response
    mock_unwrapper.unwrap_results.return_value = []

    client = PageIterableTestClient(mock_api_client, mock_unwrapper)
    client._base_url_override = "https://custom.api.com/v2"

    results = [item async for item in client.iterate()]

    assert len(results) == 0
    mock_api_client.request.assert_awaited_once()
    _, kwargs = mock_api_client.request.call_args
    assert kwargs.get("base_url_override") == "https://custom.api.com/v2"


# --- Change 1: Configurable Parameter Names ---
class OpenAlexStyleParams:
    """Mixin group with OpenAlex-style parameter names for testing overrides."""

    _param_page = "page"
    _param_page_size = "per_page"
    _param_sort = "sort"
    _param_cursor = "cursor"
    _param_id = "id"
    _param_search = "search"


class OpenAlexSearchClient(
    OpenAlexStyleParams, SearchableMixin, ConcreteResourceClient
):
    pass


class OpenAlexCursorClient(
    OpenAlexStyleParams, CursorIterableMixin, ConcreteResourceClient
):
    pass


class OpenAlexPageClient(
    OpenAlexStyleParams, PageIterableMixin, ConcreteResourceClient
):
    pass


class OpenAlexGetClient(OpenAlexStyleParams, GettableMixin, ConcreteResourceClient):
    pass


@pytest.mark.asyncio
async def test_searchable_custom_param_names(mock_api_client, mock_unwrapper):
    """SearchableMixin uses custom _param_page_size and _param_sort when overridden."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = {"results": [], "total": 0}
    mock_api_client.request.return_value = mock_response
    client = OpenAlexSearchClient(mock_api_client, mock_unwrapper)
    await client.search(page=2, page_size=50, sort_by="title asc")
    call_kwargs = mock_api_client.request.await_args[1]
    params = call_kwargs["params"]
    assert params["per_page"] == 50  # custom name
    assert params["page"] == 2  # same name
    assert params["sort"] == "title asc"  # custom name
    assert "pageSize" not in params
    assert "sortBy" not in params


@pytest.mark.asyncio
async def test_cursor_iterable_custom_param_names(mock_api_client, mock_unwrapper):
    """CursorIterableMixin uses custom _param_cursor and _param_page_size."""
    page1 = [{"id": "1", "value": "A"}]
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = {"results": page1}
    mock_api_client.request.return_value = mock_response
    mock_unwrapper.unwrap_results.return_value = page1
    mock_unwrapper.get_next_page_token.return_value = None
    client = OpenAlexCursorClient(mock_api_client, mock_unwrapper)
    [_ async for _ in client.iterate(page_size=25, sort_by="date desc")]
    call_kwargs = mock_api_client.request.await_args[1]
    params = call_kwargs["params"]
    assert params["cursor"] == "*"
    assert params["per_page"] == 25  # custom name
    assert params["sort"] == "date desc"  # custom name
    assert "pageSize" not in params
    assert "sortBy" not in params


@pytest.mark.asyncio
async def test_page_iterable_custom_param_names(mock_api_client, mock_unwrapper):
    """PageIterableMixin uses custom _param_page, _param_page_size, _param_sort."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = {"results": []}
    mock_api_client.request.return_value = mock_response
    mock_unwrapper.unwrap_results.return_value = []
    client = OpenAlexPageClient(mock_api_client, mock_unwrapper)
    [_ async for _ in client.iterate(page_size=10, sort_by="name")]
    call_kwargs = mock_api_client.request.await_args[1]
    params = call_kwargs["params"]
    assert params["per_page"] == 10  # custom name
    assert params["page"] == 1
    assert params["sort"] == "name"  # custom name
    assert "pageSize" not in params
    assert "sortBy" not in params


@pytest.mark.asyncio
async def test_gettable_custom_param_names(mock_api_client, mock_unwrapper):
    """GettableMixin.get() non-direct path uses custom _param_id and _param_page_size."""
    entity = {"id": "W123", "value": "test"}
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = {"results": [entity]}
    mock_api_client.request.return_value = mock_response
    mock_unwrapper.unwrap_results.return_value = [entity]
    client = OpenAlexGetClient(mock_api_client, mock_unwrapper)
    await client.get("W123")
    call_kwargs = mock_api_client.request.await_args[1]
    params = call_kwargs["params"]
    assert params["id"] == "W123"
    assert params["per_page"] == 1  # custom name
    assert "pageSize" not in params


@pytest.mark.asyncio
async def test_default_param_names_unchanged(mock_api_client, mock_unwrapper):
    """Default SearchableTestClient still uses original OpenAIRE param names."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = {"results": [], "total": 0}
    mock_api_client.request.return_value = mock_response
    client = SearchableTestClient(mock_api_client, mock_unwrapper)
    await client.search(page=1, page_size=20, sort_by="relevance")
    call_kwargs = mock_api_client.request.await_args[1]
    params = call_kwargs["params"]
    assert params["page"] == 1
    assert params["pageSize"] == 20
    assert params["sortBy"] == "relevance"


# --- Change 2: Pluggable Filter Serialization ---
class OpenAlexFilterClient(SearchableMixin, ConcreteResourceClient):
    """Client that overrides _serialize_filters for comma-separated filter strings."""

    _param_page_size = "per_page"
    _param_sort = "sort"

    def _serialize_filters(self, filters):
        base = super()._serialize_filters(filters)
        if not base:
            return {}
        # OpenAlex-style: combine all filters into single "filter" param
        parts = [f"{k}:{v}" for k, v in base.items()]
        return {"filter": ",".join(parts)}


@pytest.mark.asyncio
async def test_custom_serialize_filters(mock_api_client, mock_unwrapper):
    """Custom _serialize_filters produces OpenAlex-style filter string."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = {"results": [], "meta": {"count": 0}}
    mock_api_client.request.return_value = mock_response
    client = OpenAlexFilterClient(mock_api_client, mock_unwrapper)

    class WorkFilters(BaseModel):
        type: str | None = None
        author_id: str | None = None

    filters = WorkFilters(type="article", author_id="A123")
    await client.search(filters=filters)
    call_kwargs = mock_api_client.request.await_args[1]
    params = call_kwargs["params"]
    assert "filter" in params
    assert "type:article" in params["filter"]
    assert "author_id:A123" in params["filter"]


@pytest.mark.asyncio
async def test_default_serialize_filters_unchanged(mock_api_client, mock_unwrapper):
    """Default _serialize_filters produces individual params (backward compat)."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = {"results": []}
    mock_api_client.request.return_value = mock_response
    client = SearchableTestClient(mock_api_client, mock_unwrapper)

    class TestFilters(BaseModel):
        type: str | None = None
        year: int | None = None

    await client.search(filters=TestFilters(type="publication", year=2024))
    call_kwargs = mock_api_client.request.await_args[1]
    params = call_kwargs["params"]
    assert params["type"] == "publication"
    assert params["year"] == 2024


# --- Change 3: Optional search Parameter ---
@pytest.mark.asyncio
async def test_searchable_search_param(mock_api_client, mock_unwrapper):
    """SearchableMixin.search() adds search param when provided."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = {"results": [], "total": 0}
    mock_api_client.request.return_value = mock_response
    client = SearchableTestClient(mock_api_client, mock_unwrapper)
    await client.search(search="machine learning")
    call_kwargs = mock_api_client.request.await_args[1]
    params = call_kwargs["params"]
    assert params["search"] == "machine learning"


@pytest.mark.asyncio
async def test_searchable_search_param_omitted_when_none(
    mock_api_client, mock_unwrapper
):
    """SearchableMixin.search() omits search param when None (default)."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = {"results": [], "total": 0}
    mock_api_client.request.return_value = mock_response
    client = SearchableTestClient(mock_api_client, mock_unwrapper)
    await client.search()
    call_kwargs = mock_api_client.request.await_args[1]
    params = call_kwargs["params"]
    assert "search" not in params


@pytest.mark.asyncio
async def test_cursor_iterable_search_param(mock_api_client, mock_unwrapper):
    """CursorIterableMixin.iterate() adds search param when provided."""
    page1 = [{"id": "1", "value": "A"}]
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = {"results": page1}
    mock_api_client.request.return_value = mock_response
    mock_unwrapper.unwrap_results.return_value = page1
    mock_unwrapper.get_next_page_token.return_value = None
    client = CursorIterableTestClient(mock_api_client, mock_unwrapper)
    [_ async for _ in client.iterate(search="deep learning")]
    call_kwargs = mock_api_client.request.await_args[1]
    params = call_kwargs["params"]
    assert params["search"] == "deep learning"


@pytest.mark.asyncio
async def test_page_iterable_search_param(mock_api_client, mock_unwrapper):
    """PageIterableMixin.iterate() adds search param when provided."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = {"results": []}
    mock_api_client.request.return_value = mock_response
    mock_unwrapper.unwrap_results.return_value = []
    client = PageIterableTestClient(mock_api_client, mock_unwrapper)
    [_ async for _ in client.iterate(search="quantum")]
    call_kwargs = mock_api_client.request.await_args[1]
    params = call_kwargs["params"]
    assert params["search"] == "quantum"


@pytest.mark.asyncio
async def test_search_param_disabled_when_param_search_empty(
    mock_api_client, mock_unwrapper
):
    """When _param_search is empty string, search param is not added."""

    class NoSearchClient(SearchableMixin, ConcreteResourceClient):
        _param_search = ""

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = {"results": [], "total": 0}
    mock_api_client.request.return_value = mock_response
    client = NoSearchClient(mock_api_client, mock_unwrapper)
    await client.search(search="ignored")
    call_kwargs = mock_api_client.request.await_args[1]
    params = call_kwargs["params"]
    assert "search" not in params
    assert "ignored" not in str(params)
