"""Tests for StavrophoraSession."""

import pytest
from bibliofabric.auth import QueryParameterAuth

from stavrophora.client import StavrophoraClient
from stavrophora.config import StavrophoraSettings
from stavrophora.session import StavrophoraSession


@pytest.mark.asyncio
async def test_session_context_manager():
    """StavrophoraSession works as an async context manager and closes on exit."""
    async with StavrophoraSession() as s:
        assert s._api_client is not None
        assert isinstance(s._api_client, StavrophoraClient)
        # Client is not closed while inside context
        assert not s._api_client._http_client.is_closed

    # After exit the underlying HTTP client should be closed
    assert s._api_client._http_client.is_closed


@pytest.mark.asyncio
async def test_session_with_mailto():
    """StavrophoraSession(mailto=...) should use QueryParameterAuth."""
    async with StavrophoraSession(mailto="test@example.org") as s:
        auth = s._api_client._auth_strategy
        assert isinstance(auth, QueryParameterAuth)
        assert auth._key_name == "mailto"
        assert auth._key_value == "test@example.org"


@pytest.mark.asyncio
async def test_session_without_mailto_uses_no_auth():
    async with StavrophoraSession() as s:
        auth = s._api_client._auth_strategy
        assert auth.__class__.__name__ == "NoAuth"


@pytest.mark.asyncio
async def test_session_delegates_to_client():
    """session.works etc. should delegate to the underlying client via __getattr__."""
    async with StavrophoraSession() as s:
        works_client = s.works
        assert works_client is s._api_client.works

        journals_client = s.journals
        assert journals_client is s._api_client.journals

        # Accessing an unknown attribute raises AttributeError
        with pytest.raises(AttributeError, match="StavrophoraSession"):
            _ = s.nonexistent_attr


@pytest.mark.asyncio
async def test_session_custom_settings():
    """StavrophoraSession(settings=...) should use those settings."""
    custom = StavrophoraSettings(user_agent="test-agent/1.0", mailto="x@example.org")
    async with StavrophoraSession(settings=custom) as s:
        assert s._settings is custom
        assert s._settings.user_agent == "test-agent/1.0"
        assert s._api_client._settings is custom
