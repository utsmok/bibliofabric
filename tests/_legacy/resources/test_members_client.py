"""Tests for MembersClient."""

import pytest

from stavrophora.models import Member
from stavrophora.resources.members_client import MembersClient

from .conftest import _mock_response

MEMBER = {
    "id": 78,
    "primary-name": "Elsevier BV",
    "names": ["Elsevier BV"],
    "prefixes": ["10.1016"],
    "counts": {"total-dois": 100, "current-dois": 90, "backfile-dois": 10},
}


@pytest.fixture
def members_client(mock_api_client):
    return MembersClient(mock_api_client)


@pytest.mark.asyncio
async def test_get_member(members_client, mock_api_client):
    mock_api_client.request.return_value = _mock_response({"message": MEMBER})
    member = await members_client.get("78")
    assert isinstance(member, Member)
    assert member.primary_name == "Elsevier BV"
    assert member.id == 78
    assert mock_api_client.request.call_args.args[1] == "members/78"


@pytest.mark.asyncio
async def test_search_members(members_client, mock_api_client):
    mock_api_client.request.return_value = _mock_response(
        {"message": {"total-results": 1, "items": [MEMBER]}}
    )
    response = await members_client.search(search="elsevier")
    assert response.message.total_results == 1
