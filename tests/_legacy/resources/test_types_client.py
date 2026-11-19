"""Tests for TypesClient."""

import pytest

from stavrophora.models import CrossRefType
from stavrophora.resources.types_client import TypesClient

from .conftest import _mock_response

TYPE = {"id": "journal-article", "label": "Journal Article"}


@pytest.fixture
def types_client(mock_api_client):
    return TypesClient(mock_api_client)


@pytest.mark.asyncio
async def test_get_type(types_client, mock_api_client):
    mock_api_client.request.return_value = _mock_response({"message": TYPE})
    result = await types_client.get("journal-article")
    assert isinstance(result, CrossRefType)
    assert result.id == "journal-article"
    assert result.label == "Journal Article"
    assert mock_api_client.request.call_args.args[1] == "types/journal-article"


@pytest.mark.asyncio
async def test_list_types(types_client, mock_api_client):
    mock_api_client.request.return_value = _mock_response(
        {"message": {"total-results": 1, "items": [TYPE]}}
    )
    response = await types_client.search(page_size=50)
    assert response.message.items[0].id == "journal-article"
