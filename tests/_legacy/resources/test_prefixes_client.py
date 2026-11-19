"""Tests for PrefixesClient (get + scoped works only — no list route upstream)."""

import pytest

from stavrophora.models import Prefix
from stavrophora.resources.prefixes_client import PrefixesClient
from stavrophora.resources.works_client import ScopedWorksClient

from .conftest import _mock_response

PREFIX = {
    "member": "https://id.crossref.org/member/78",
    "name": "Elsevier BV",
    "prefix": "https://id.crossref.org/prefix/10.1016",
}


@pytest.fixture
def prefixes_client(mock_api_client):
    return PrefixesClient(mock_api_client)


@pytest.mark.asyncio
async def test_get_prefix(prefixes_client, mock_api_client):
    mock_api_client.request.return_value = _mock_response({"message": PREFIX})
    result = await prefixes_client.get("10.1016")
    assert isinstance(result, Prefix)
    assert result.name == "Elsevier BV"
    # /prefixes/{prefix} returns id.crossref.org URIs; model normalizes to bare values.
    assert result.member == "78"
    assert result.prefix == "10.1016"
    assert mock_api_client.request.call_args.args[1] == "prefixes/10.1016"


def test_prefix_normalizes_bare_values_too():
    result = Prefix.model_validate({"member": "297", "name": "S", "prefix": "10.1038"})
    assert result.member == "297" and result.prefix == "10.1038"


@pytest.mark.asyncio
async def test_no_list_route(prefixes_client):
    """Crossref serves no /prefixes list route; search must be refused."""
    from bibliofabric.exceptions import BibliofabricError

    with pytest.raises(BibliofabricError, match="list route"):
        await prefixes_client.search()


def test_scoped_works_path(prefixes_client):
    scoped = prefixes_client.works("10.1016")
    assert isinstance(scoped, ScopedWorksClient)
    assert scoped._entity_path == "prefixes/10.1016/works"
