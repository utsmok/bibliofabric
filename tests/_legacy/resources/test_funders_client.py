"""Tests for FundersClient, including scoped works."""

import pytest

from stavrophora.models import Funder
from stavrophora.resources.funders_client import FundersClient
from stavrophora.resources.works_client import ScopedWorksClient

from .conftest import _mock_response

FUNDER = {
    "id": "10.13039/501100001711",
    "name": "Swiss National Science Foundation",
    "tokens": ["swiss", "national", "science", "foundation"],
    "alt-names": ["SNF", "SNSF"],
}


@pytest.fixture
def funders_client(mock_api_client):
    return FundersClient(mock_api_client)


@pytest.mark.asyncio
async def test_get_funder(funders_client, mock_api_client):
    mock_api_client.request.return_value = _mock_response({"message": FUNDER})
    funder = await funders_client.get("10.13039/501100001711")
    assert isinstance(funder, Funder)
    assert funder.name == "Swiss National Science Foundation"
    assert funder.alt_names == ["SNF", "SNSF"]
    assert mock_api_client.request.call_args.args[1] == "funders/10.13039/501100001711"


@pytest.mark.asyncio
async def test_get_funder_encodes_doi(funders_client, mock_api_client):
    mock_api_client.request.return_value = _mock_response({"message": FUNDER})
    await funders_client.get("https://doi.org/10.13039/501100001711")
    assert mock_api_client.request.call_args.args[1] == "funders/10.13039/501100001711"


def test_scoped_works_path(funders_client):
    scoped = funders_client.works("10.13039/501100001711")
    assert isinstance(scoped, ScopedWorksClient)
    assert scoped._entity_path == "funders/10.13039/501100001711/works"
