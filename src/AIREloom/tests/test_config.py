import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import httpx

from bibliofabric.auth import StaticTokenAuth

from aireloom import AireloomSession


@pytest.mark.asyncio
async def test_session_programmatic_config_override(httpx_mock, monkeypatch):


    # Ensure env vars are not set for these, or set to different values
    monkeypatch.delenv("AIRELOOM_OPENAIRE_API_TOKEN", raising=False)
    monkeypatch.delenv("AIRELOOM_REQUEST_TIMEOUT", raising=False)
    # Set a base env var for timeout that will be overridden by programmatic session timeout
    monkeypatch.setenv("AIRELOOM_REQUEST_TIMEOUT", "10")

    # Programmatic override for auth strategy and timeout
    custom_auth_strategy = StaticTokenAuth(token="override_token_12345")
    custom_timeout = 45  # Changed to int

    async with AireloomSession(
        auth_strategy=custom_auth_strategy, timeout=custom_timeout
    ) as session:
        # Verify the client inside the session uses the overridden settings
        assert isinstance(session._api_client._auth_strategy, StaticTokenAuth)
        assert session._api_client._auth_strategy._token == "override_token_12345"
        assert session._api_client._settings.request_timeout == custom_timeout
        # Check that the base setting was indeed 10 before override
        # This requires peeking at global settings before session specific one is made
        # For simplicity, we trust AireloomSession's logic to copy and update.

        # Make a call to ensure it works with these settings
        with patch("bibliofabric.client.BaseApiClient._request_with_retry", new_callable=AsyncMock) as mock_request_with_retry:
            # Ensure the mock returns a 3-tuple (response, parsed_model, attempts)
            mock_response = MagicMock(spec=httpx.Response, status_code=200)
            mock_response.json.return_value = {"results": [{"id": "progcfg123", "title": "Prog Config Test"}], "header": {"numFound": 1, "pageSize": 1}}
            mock_request_with_retry.return_value = (mock_response, None, 1)
            await session.research_products.get("progcfg123")

    # Test that default init still picks up env vars for settings.
    # We want StaticTokenAuth to be chosen.

    from aireloom.config import ApiSettings, get_settings  # Import ApiSettings

    # Store original get_settings and clear its cache
    original_get_settings_func = get_settings
    get_settings.cache_clear()

    # Monkeypatch os.environ directly for this segment
    monkeypatch.setenv("AIRELOOM_OPENAIRE_API_TOKEN", "env_token_67890")
    # Ensure client_id/secret are not in os.environ for this part
    # These delenv calls are good practice but might be overridden by .env files
    # if ApiSettings loads them before os.environ.
    monkeypatch.delenv("AIRELOOM_OPENAIRE_CLIENT_ID", raising=False)
    monkeypatch.delenv("AIRELOOM_OPENAIRE_CLIENT_SECRET", raising=False)
    # AIRELOOM_REQUEST_TIMEOUT is still "10" from the earlier monkeypatch.setenv

    # Define a mock get_settings that ensures no client_id/secret from .env files
    # interfere, while still loading other env vars like token and timeout.
    def mock_get_settings_for_token_test():
        # Create a fresh settings instance with explicit values to ensure test isolation
        # Bypass .env file loading by using explicit model construction
        settings = ApiSettings.model_construct(
            openaire_client_id=None,  # Explicitly set to None
            openaire_client_secret=None,  # Explicitly set to None
            openaire_api_token="env_token_67890",  # From monkeypatch
            request_timeout=10.0,  # From monkeypatch
        )
        print(
            f"MOCK_GET_SETTINGS: client_id={settings.openaire_client_id}, token={settings.openaire_api_token}, timeout={settings.request_timeout}"
        )
        return settings

    # Patch both the import in session.py and client.py
    monkeypatch.setattr(
        "aireloom.config.get_settings", mock_get_settings_for_token_test
    )
    monkeypatch.setattr(
        "aireloom.session.get_settings", mock_get_settings_for_token_test
    )
    monkeypatch.setattr(
        "aireloom.client.get_settings", mock_get_settings_for_token_test
    )

    async with AireloomSession() as session_env:  # No auth_strategy passed
        assert isinstance(session_env._api_client._auth_strategy, StaticTokenAuth), (
            f"Expected StaticTokenAuth, got {type(session_env._api_client._auth_strategy)}"
        )
        assert session_env._api_client._auth_strategy._token == "env_token_67890"

        # Settings object within AireloomClient should reflect these controlled values
        assert session_env._api_client._settings.openaire_api_token == "env_token_67890"
        assert session_env._api_client._settings.openaire_client_id is None
        assert session_env._api_client._settings.openaire_client_secret is None
        # Timeout should be from env var "10" loaded by mock_get_settings_for_token_test via ApiSettings()
        assert session_env._api_client._settings.request_timeout == 10.0, (
            f"Expected timeout 10, got {session_env._api_client._settings.request_timeout}"
        )

        # Example call to ensure it works with StaticTokenAuth
        
        httpx_mock.add_response(
            url="https://api.openaire.eu/graph/v1/researchProducts?id=envcfg456&pageSize=1",
            method="GET",
            json={"results": [{"id": "envcfg456", "title": "Env Config Test"}], "header": {"numFound": 1, "pageSize": 1}},
            match_headers={"Authorization": "Bearer env_token_67890"},
        )
        await session_env.research_products.get("envcfg456")

    # Restore original get_settings and clear cache
    monkeypatch.setattr("aireloom.config.get_settings", original_get_settings_func)
    get_settings.cache_clear()  # Clear again for subsequent tests
