"""Tests for StavrophoraClient."""

import pytest
from bibliofabric.auth import NoAuth, QueryParameterAuth

from stavrophora.client import StavrophoraClient
from stavrophora.config import StavrophoraSettings
from stavrophora.constants import CROSSREF_API_BASE_URL
from stavrophora.resources import (
    FundersClient,
    JournalsClient,
    LicensesClient,
    MembersClient,
    PrefixesClient,
    TypesClient,
    WorksClient,
)


@pytest.mark.asyncio
async def test_context_manager_enter_exit():
    """Async context manager should open then close the HTTP client."""
    async with StavrophoraClient() as client:
        assert not client._http_client.is_closed
    assert client._http_client.is_closed


def test_mailto_uses_query_parameter_auth():
    """mailto should be sent as a mailto query parameter (polite pool)."""
    client = StavrophoraClient(mailto="test@example.org")
    assert isinstance(client._auth_strategy, QueryParameterAuth)
    assert client._auth_strategy._key_name == "mailto"
    assert client._auth_strategy._key_value == "test@example.org"


def test_no_mailto_defaults_to_no_auth():
    client = StavrophoraClient()
    assert isinstance(client._auth_strategy, NoAuth)


def test_mailto_from_settings():
    settings = StavrophoraSettings(mailto="settings@example.org")
    client = StavrophoraClient(settings=settings)
    auth = client._auth_strategy
    assert isinstance(auth, QueryParameterAuth)
    assert auth._key_value == "settings@example.org"


def test_explicit_auth_strategy_override():
    """Passing auth_strategy should override mailto resolution."""
    client = StavrophoraClient(mailto="test@example.org", auth_strategy=NoAuth())
    assert isinstance(client._auth_strategy, NoAuth)


def test_base_url():
    client = StavrophoraClient()
    assert client._base_url == CROSSREF_API_BASE_URL
    custom = StavrophoraClient(base_url="https://example.org/v1")
    assert custom._base_url == "https://example.org/v1"


def test_resource_client_properties():
    """Lazy-loaded resource properties should return correct client types."""
    client = StavrophoraClient()
    assert isinstance(client.works, WorksClient)
    assert isinstance(client.journals, JournalsClient)
    assert isinstance(client.funders, FundersClient)
    assert isinstance(client.members, MembersClient)
    assert isinstance(client.types, TypesClient)
    assert isinstance(client.prefixes, PrefixesClient)
    assert isinstance(client.licenses, LicensesClient)
