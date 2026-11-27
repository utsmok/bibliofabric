"""Credential wiring, settings defaults, and rate-class routing."""

from typing import Any

import httpx
import pytest
from aletheca import (
    AlethecaClient,
    AlethecaSettings,
    APIError,
    AuthError,
    ConfigurationError,
)
from bibliofabric.auth import NoAuth

from ..conftest import entity


def keyless(settings) -> AlethecaClient:
    return AlethecaClient(settings=settings.model_copy(update={"api_key": None}))


async def test_default_scheme_sends_api_key_query_param(client, httpx_mock):
    httpx_mock.add_response(json=entity("W1"))
    await client.works.get("W1")
    request = httpx_mock.get_requests()[-1]
    assert request.url.params["api_key"] == "test-key"
    assert "authorization" not in request.headers


async def test_bearer_scheme_sends_authorization_header(settings, httpx_mock):
    async with AlethecaClient(
        settings=settings.model_copy(update={"auth_scheme": "bearer"})
    ) as bearer_client:
        httpx_mock.add_response(json=entity("W1"))
        await bearer_client.works.get("W1")
    request = httpx_mock.get_requests()[-1]
    assert request.headers["authorization"] == "Bearer test-key"
    assert "api_key" not in request.url.params


async def test_keyless_client_sends_no_credential(settings, httpx_mock):
    async with keyless(settings) as anon_client:
        httpx_mock.add_response(json=entity("W1"))
        await anon_client.works.get("W1")
    request = httpx_mock.get_requests()[-1]
    assert "api_key" not in request.url.params
    assert "authorization" not in request.headers


async def test_empty_api_key_arg_forces_keyless_and_actionable_401(
    settings, httpx_mock
):
    httpx_mock.add_response(status_code=401, json={})
    async with AlethecaClient(settings=settings, api_key="") as anon_client:
        with pytest.raises(AuthError) as excinfo:
            await anon_client.works.search()
        assert type(anon_client).__name__ in str(excinfo.value)
    request = httpx_mock.get_requests()[-1]
    assert "api_key" not in request.url.params


async def test_empty_settings_api_key_marks_keyless(settings, httpx_mock):
    httpx_mock.add_response(status_code=401, json={})
    empty_settings = settings.model_copy(update={"api_key": ""})
    async with AlethecaClient(settings=empty_settings) as anon_client:
        with pytest.raises(AuthError) as excinfo:
            await anon_client.works.search()
        assert "ALETHECA_API_KEY" in str(excinfo.value)


async def test_unknown_auth_scheme_raises_configuration_error(settings):
    bad_scheme: Any = "header"
    with pytest.raises(ConfigurationError, match="auth_scheme"):
        AlethecaClient(settings=settings, auth_scheme=bad_scheme)


async def test_explicit_strategy_wins_over_key(settings, httpx_mock):
    async with AlethecaClient(
        settings=settings, auth_strategy=NoAuth(), api_key="ignored"
    ) as custom_client:
        httpx_mock.add_response(json=entity("W1"))
        await custom_client.works.get("W1")
    request = httpx_mock.get_requests()[-1]
    assert "api_key" not in request.url.params


async def test_keyless_401_gets_actionable_message(settings, httpx_mock):
    httpx_mock.add_response(status_code=401, json={})
    async with keyless(settings) as anon_client:
        with pytest.raises(AuthError) as excinfo:
            await anon_client.works.search()
        message = str(excinfo.value)
        assert "ALETHECA_API_KEY" in message
        assert "api_key=" in message
        assert type(anon_client).__name__ in message


async def test_keyed_401_keeps_upstream_message(client, httpx_mock):
    httpx_mock.add_response(status_code=401, json={})
    with pytest.raises(AuthError) as excinfo:
        await client.works.search()
    assert "Get a free API key" not in str(excinfo.value)


async def test_error_str_redacts_credential(client, httpx_mock):
    httpx_mock.add_response(status_code=500, json={})
    with pytest.raises(APIError) as excinfo:
        await client.works.search()
    assert "test-key" not in str(excinfo.value)
    assert "test-key" not in excinfo.value.message


async def test_http_client_injection_forwarded(settings, httpx_mock):
    httpx_mock.add_response(json=entity("W1"))
    async with httpx.AsyncClient() as injected:
        async with AlethecaClient(settings=settings, http_client=injected) as custom:
            work = await custom.works.get("W1")
            assert work.id == "https://openalex.org/W1"
        assert not injected.is_closed


def test_settings_defaults_and_overrides():
    defaults = AlethecaSettings(_env_file=None)
    assert defaults.max_requests_per_second == 10.0
    assert defaults.max_concurrency == 5
    assert defaults.rate_limits == {"semantic": 1.0}

    explicit_10 = AlethecaSettings(_env_file=None, max_concurrency=10)
    assert explicit_10.max_concurrency == 10

    unthrottled = AlethecaSettings(_env_file=None, max_requests_per_second=None)
    assert unthrottled.max_requests_per_second is None
    assert unthrottled.rate_limits == {}

    secret_settings = AlethecaSettings(_env_file=None, api_key="super-secret-key")
    assert "super-secret-key" not in repr(secret_settings)


async def test_rate_class_routes_semantic_search(client):
    normal = httpx.Request("GET", "https://api.openalex.org/works?search=ai")
    semantic = httpx.Request(
        "GET", "https://api.openalex.org/works?search.semantic=embeddings"
    )
    assert client.rate_class(normal) == "default"
    assert client.rate_class(semantic) == "semantic"
