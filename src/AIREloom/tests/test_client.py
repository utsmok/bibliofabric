import json
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from bibliofabric.auth import (
    AuthStrategy,
    ClientCredentialsAuth,
    NoAuth,
    StaticTokenAuth,
)
from bibliofabric.client import BaseApiClient
from bibliofabric.exceptions import (
    APIError,
    BibliofabricError,
    RateLimitError,
    TimeoutError,
)

from aireloom.client import AireloomClient
from aireloom.config import ApiSettings
from aireloom.unwrapper import OpenAireUnwrapper


@pytest.fixture
def mock_settings_with_creds():
    return ApiSettings(
        openaire_client_id="test_id",
        openaire_client_secret="test_secret",
        openaire_token_url="https://test.token.url",
    )


@pytest.fixture
def mock_api_client_fixture():
    """Fixture to create a mock AireloomClient."""
    mock_client = AsyncMock(spec=AireloomClient)
    mock_client._response_unwrapper = OpenAireUnwrapper()
    mock_http_response = AsyncMock(spec=httpx.Response)
    mock_http_response.status_code = 200
    mock_http_response.json.return_value = {
        "header": {
            "numFound": 0,
            "pageSize": 10,
            "pageNumber": 1,
            "totalPages": 0,
            "nextCursor": None,
        },
        "results": [],
    }
    mock_client.request.return_value = mock_http_response
    return mock_client

