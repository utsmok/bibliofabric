# tests/resources/test_scholix_client.py
from unittest.mock import AsyncMock, call

import httpx  # Import httpx
import pytest
from bibliofabric.exceptions import BibliofabricError  # Added ValidationError

from aireloom.constants import DEFAULT_PAGE_SIZE, OPENAIRE_SCHOLIX_API_BASE_URL
from aireloom.endpoints import SCHOLIX, ScholixFilters
from aireloom.models import (
    ScholixRelationship,  # Added
)
from aireloom.resources import ScholixClient


@pytest.fixture
def mock_api_client_fixture():  # Renamed
    """Fixture to create a mock AireloomClient."""
    mock_client = AsyncMock()
    mock_http_response = AsyncMock(spec=httpx.Response)
    mock_http_response.status_code = 200
    # Default Scholix response for mock
    mock_http_response.json.return_value = {
        "currentPage": 0,
        "totalPages": 0,
        "totalLinks": 0,
        "result": [],
    }
    mock_client.request.return_value = mock_http_response
    return mock_client


@pytest.fixture
def scholix_client(mock_api_client_fixture: AsyncMock) -> ScholixClient:
    """Fixture to create a ScholixClient with a mocked API client."""
    return ScholixClient(api_client=mock_api_client_fixture)


# Helper to create ScholixRelationship test data
def create_mock_scholix_link_data(
    source_pid: str, target_pid: str, rel_type: str = "References"
) -> dict:
    return {
        "LinkProvider": [{"Name": "Test Provider"}],
        "LinkPublicationDate": "2023-01-01T00:00:00Z",
        "RelationshipType": {"Name": rel_type},
        "Source": {
            "Identifier": [{"ID": source_pid, "IDScheme": "doi"}],
            "Type": "publication",
        },
        "Target": {
            "Identifier": [{"ID": target_pid, "IDScheme": "doi"}],
            "Type": "dataset",
        },
    }


@pytest.mark.asyncio
async def test_search_scholix_links(
    scholix_client: ScholixClient, mock_api_client_fixture: AsyncMock
):
    """Test searching for Scholix links."""
    source_pid_val = "10.1234/source.pid"
    target_pid_val = "10.5678/target.pid"
    page_size = 5
    page_number = 0  # Scholix is 0-indexed

    mock_link_dict = create_mock_scholix_link_data(source_pid_val, target_pid_val)
    expected_results_data = [mock_link_dict]
    expected_link_model = ScholixRelationship.model_validate(mock_link_dict)

    mock_api_response_dict = {
        "currentPage": page_number,
        "totalPages": 1,
        "totalLinks": 1,
        "result": expected_results_data,
    }
    mock_http_response = AsyncMock(spec=httpx.Response)
    mock_http_response.status_code = 200
    mock_http_response.json.return_value = mock_api_response_dict
    mock_api_client_fixture.request.return_value = mock_http_response

    filters = ScholixFilters(sourcePid=source_pid_val)
    response = await scholix_client.search_links(
        filters=filters, page=page_number, page_size=page_size
    )

    expected_params = {
        "sourcePid": source_pid_val,
        "page": page_number,
        "rows": page_size,
    }
    mock_api_client_fixture.request.assert_called_once_with(
        method="GET",
        path=SCHOLIX,
        params=expected_params,
        base_url_override=OPENAIRE_SCHOLIX_API_BASE_URL,
        data=None,  # Added missing args
        json_data=None,  # Added missing args
    )
    assert response is not None
    assert response.result is not None
    assert len(response.result) == 1
    assert response.result[0] == expected_link_model
    assert response.current_page == page_number
    assert response.total_links == 1
    assert response.total_pages == 1


@pytest.mark.asyncio
async def test_search_scholix_links_missing_pid_filter(scholix_client: ScholixClient):
    """Test search_links raises ValueError if no PID filter is provided."""
    with pytest.raises(ValueError) as exc_info:
        await scholix_client.search_links(filters=ScholixFilters())  # Empty filters
    assert "Either sourcePid or targetPid must be provided" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info_none:
        await scholix_client.search_links(filters=None)  # No filters
    assert "Either sourcePid or targetPid must be provided" in str(exc_info_none.value)


@pytest.mark.asyncio
async def test_iterate_scholix_links(
    scholix_client: ScholixClient, mock_api_client_fixture: AsyncMock
):
    """Test iterating through Scholix links."""
    target_pid_val = "10.9876/target.pid"
    page_size = 1

    link1_dict = create_mock_scholix_link_data(
        "10.111/source1", target_pid_val, "IsReferencedBy"
    )
    link2_dict = create_mock_scholix_link_data(
        "10.222/source2", target_pid_val, "IsSupplementTo"
    )

    expected_link1_model = ScholixRelationship.model_validate(link1_dict)
    expected_link2_model = ScholixRelationship.model_validate(link2_dict)

    page1_response_dict = {
        "currentPage": 0,
        "totalPages": 2,
        "totalLinks": 2,
        "result": [link1_dict],
    }
    page2_response_dict = {
        "currentPage": 1,
        "totalPages": 2,
        "totalLinks": 2,
        "result": [link2_dict],
    }

    mock_http_response_page1 = AsyncMock(spec=httpx.Response)
    mock_http_response_page1.status_code = 200
    mock_http_response_page1.json.return_value = page1_response_dict

    mock_http_response_page2 = AsyncMock(spec=httpx.Response)
    mock_http_response_page2.status_code = 200
    mock_http_response_page2.json.return_value = page2_response_dict

    mock_api_client_fixture.request.side_effect = [
        mock_http_response_page1,
        mock_http_response_page2,
    ]

    iterated_links = []
    filters = ScholixFilters(targetPid=target_pid_val)
    async for link in scholix_client.iterate_links(
        filters=filters, page_size=page_size
    ):
        iterated_links.append(link)

    assert len(iterated_links) == 2
    assert iterated_links[0] == expected_link1_model
    assert iterated_links[1] == expected_link2_model

    expected_calls = [
        call(
            method="GET",
            path=SCHOLIX,
            params={"targetPid": target_pid_val, "rows": page_size, "page": 0},
            base_url_override=OPENAIRE_SCHOLIX_API_BASE_URL,
            data=None,
            json_data=None,
        ),
        call(
            method="GET",
            path=SCHOLIX,
            params={"targetPid": target_pid_val, "rows": page_size, "page": 1},
            base_url_override=OPENAIRE_SCHOLIX_API_BASE_URL,
            data=None,
            json_data=None,
        ),
    ]
    mock_api_client_fixture.request.assert_has_calls(expected_calls)
    assert mock_api_client_fixture.request.call_count == 2


@pytest.mark.asyncio
async def test_iterate_scholix_links_no_results(
    scholix_client: ScholixClient, mock_api_client_fixture: AsyncMock
):
    """Test iterating Scholix links when the search yields no results."""
    source_pid_val = "10.000/no.links.here"
    page_size = DEFAULT_PAGE_SIZE

    mock_api_response_dict = {
        "currentPage": 0,
        "totalPages": 0,
        "totalLinks": 0,
        "result": [],
    }
    mock_http_response = AsyncMock(spec=httpx.Response)
    mock_http_response.status_code = 200
    mock_http_response.json.return_value = mock_api_response_dict
    mock_api_client_fixture.request.return_value = mock_http_response

    count = 0
    filters = ScholixFilters(sourcePid=source_pid_val)
    async for _ in scholix_client.iterate_links(filters=filters, page_size=page_size):
        count += 1

    assert count == 0
    expected_params = {"sourcePid": source_pid_val, "page": 0, "rows": page_size}
    mock_api_client_fixture.request.assert_called_once_with(
        method="GET",
        path=SCHOLIX,
        params=expected_params,
        base_url_override=OPENAIRE_SCHOLIX_API_BASE_URL,
        data=None,
        json_data=None,
    )


@pytest.mark.asyncio
async def test_iterate_scholix_links_api_error(
    scholix_client: ScholixClient, mock_api_client_fixture: AsyncMock
):
    """Test API error during Scholix link iteration."""
    target_pid_val = "10.error/target"
    page_size = 1

    link_data_page1 = create_mock_scholix_link_data("10.source/page1", target_pid_val)
    expected_link_model_page1 = ScholixRelationship.model_validate(link_data_page1)

    page1_response_dict = {
        "currentPage": 0,
        "totalPages": 2,
        "totalLinks": 2,
        "result": [link_data_page1],
    }
    mock_http_response_page1 = AsyncMock(spec=httpx.Response)
    mock_http_response_page1.status_code = 200
    mock_http_response_page1.json.return_value = page1_response_dict

    error_response_mock = AsyncMock(spec=httpx.Response)
    error_response_mock.status_code = 500
    error_response_mock.request = httpx.Request("GET", f"/{SCHOLIX}")
    error_response_mock.json.return_value = {"error": "scholix server down"}

    mock_api_client_fixture.request.side_effect = [
        mock_http_response_page1,
        httpx.HTTPStatusError(
            message="Scholix Server Error '500'",
            request=error_response_mock.request,
            response=error_response_mock,
        ),
    ]

    iterated_links = []
    filters = ScholixFilters(targetPid=target_pid_val)
    with pytest.raises(BibliofabricError) as exc_info:
        async for link in scholix_client.iterate_links(
            filters=filters, page_size=page_size
        ):
            iterated_links.append(link)

    assert len(iterated_links) == 1
    assert iterated_links[0] == expected_link_model_page1
    assert f"Unexpected error searching {SCHOLIX}: Scholix Server Error '500'" in str(
        exc_info.value
    )

    expected_calls = [
        call(
            method="GET",
            path=SCHOLIX,
            params={"targetPid": target_pid_val, "rows": page_size, "page": 0},
            base_url_override=OPENAIRE_SCHOLIX_API_BASE_URL,
            data=None,
            json_data=None,
        ),
        call(
            method="GET",
            path=SCHOLIX,
            params={"targetPid": target_pid_val, "rows": page_size, "page": 1},
            base_url_override=OPENAIRE_SCHOLIX_API_BASE_URL,
            data=None,
            json_data=None,
        ),
    ]
    mock_api_client_fixture.request.assert_has_calls(expected_calls)
    assert mock_api_client_fixture.request.call_count == 2
