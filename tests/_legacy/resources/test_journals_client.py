"""Tests for JournalsClient, including scoped works."""

import pytest

from stavrophora.models import Journal
from stavrophora.resources.journals_client import JournalsClient
from stavrophora.resources.works_client import ScopedWorksClient

from .conftest import _mock_response

JOURNAL = {
    "title": ["Nature"],
    "publisher": "Springer Science and Business Media LLC",
    "ISSN": ["0028-0836", "1476-4687"],
    "counts": {"total-dois": 0, "current-dois": 0, "backfile-dois": 423248},
}


@pytest.fixture
def journals_client(mock_api_client):
    return JournalsClient(mock_api_client)


@pytest.mark.asyncio
async def test_get_journal(journals_client, mock_api_client):
    mock_api_client.request.return_value = _mock_response({"message": JOURNAL})
    journal = await journals_client.get("0028-0836")
    assert isinstance(journal, Journal)
    assert journal.primary_title == "Nature"
    assert journal.issn == ["0028-0836", "1476-4687"]
    assert mock_api_client.request.call_args.args[1] == "journals/0028-0836"


@pytest.mark.asyncio
async def test_search_journals(journals_client, mock_api_client):
    mock_api_client.request.return_value = _mock_response(
        {"message": {"total-results": 1, "items": [JOURNAL]}}
    )
    response = await journals_client.search(search="nature", page_size=5)
    assert response.message.items[0].publisher.startswith("Springer")
    params = mock_api_client.request.call_args.kwargs["params"]
    assert params["query"] == "nature"
    assert params["rows"] == 5


def test_scoped_works_path(journals_client):
    scoped = journals_client.works("0028-0836")
    assert isinstance(scoped, ScopedWorksClient)
    assert scoped._entity_path == "journals/0028-0836/works"


@pytest.mark.asyncio
async def test_scoped_works_search(journals_client, mock_api_client):
    mock_api_client.request.return_value = _mock_response(
        {"message": {"total-results": 0, "items": []}}
    )
    scoped = journals_client.works("0028-0836")
    await scoped.search(page_size=3, sort_by="published:desc")
    path = mock_api_client.request.call_args.args[1]
    params = mock_api_client.request.call_args.kwargs["params"]
    assert path == "journals/0028-0836/works"
    assert params["rows"] == 3
    assert params["sort"] == "published"
    assert params["order"] == "desc"
