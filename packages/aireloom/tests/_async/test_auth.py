"""Credential wiring: Keycloak client-credentials flow and anonymous mode."""

import httpx
import pytest
from aireloom import AireloomClient, AireloomSettings
from bibliofabric.auth import NoAuth

from .conftest import TOKEN_URL, json_response, load, make_settings, params_of


async def test_anonymous_sends_no_auth_header(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("rp_page.json")))
    await client.research_products.search()
    request = httpx_mock.get_request()
    assert "authorization" not in request.headers


async def test_client_credentials_fetches_bearer_token(httpx_mock):
    httpx_mock.add_response(
        url=TOKEN_URL, json={"access_token": "tok123", "expires_in": 3600}
    )
    httpx_mock.add_response(**json_response(load("rp_page.json")))
    settings = make_settings(openaire_client_id="cid", openaire_client_secret="secret")
    async with AireloomClient(settings=settings) as client:
        await client.research_products.search()

    token_request = httpx_mock.get_requests()[0]
    assert token_request.method == "POST"
    assert token_request.url == TOKEN_URL
    assert b"grant_type=client_credentials" in token_request.read()
    assert token_request.headers["authorization"].startswith("Basic ")

    graph_request = httpx_mock.get_requests()[1]
    assert graph_request.headers["authorization"] == "Bearer tok123"


async def test_explicit_auth_strategy_wins(httpx_mock):
    httpx_mock.add_response(**json_response(load("rp_page.json")))
    settings = make_settings(openaire_client_id="cid", openaire_client_secret="secret")
    async with AireloomClient(settings=settings, auth=NoAuth()) as client:
        await client.research_products.search()
    assert len(httpx_mock.get_requests()) == 1
    assert "authorization" not in httpx_mock.get_request().headers


async def test_credentials_come_from_environment(monkeypatch):
    monkeypatch.setenv("AIRELOOM_OPENAIRE_CLIENT_ID", "env-id")
    monkeypatch.setenv("AIRELOOM_OPENAIRE_CLIENT_SECRET", "env-secret")
    settings = AireloomSettings(_env_file=None)
    assert settings.openaire_client_id == "env-id"
    assert settings.openaire_client_secret == "env-secret"


async def test_constructor_kwargs_override_settings(httpx_mock):
    httpx_mock.add_response(
        url=TOKEN_URL, json={"access_token": "kw-tok", "expires_in": 3600}
    )
    httpx_mock.add_response(**json_response(load("rp_page.json")))
    async with httpx.AsyncClient() as injected:
        async with AireloomClient(
            settings=make_settings(),
            mailto="kw@example.org",
            client_id="kw-id",
            client_secret="kw-secret",
            http_client=injected,
        ) as client:
            await client.research_products.search()
        assert not injected.is_closed
    graph_req = httpx_mock.get_requests()[1]
    assert graph_req.headers["authorization"] == "Bearer kw-tok"
    assert params_of(graph_req)["mailto"] == "kw@example.org"


async def test_aclose_closes_scholix_even_if_graph_close_raises(monkeypatch):
    client = AireloomClient(settings=make_settings())
    scholix_closed = False
    original_close = client._scholix_api.aclose

    async def boom() -> None:
        raise RuntimeError("graph close failed")

    async def track_scholix_close() -> None:
        nonlocal scholix_closed
        scholix_closed = True
        await original_close()

    monkeypatch.setattr(client._http_client, "aclose", boom)
    monkeypatch.setattr(client._scholix_api, "aclose", track_scholix_close)

    with pytest.raises(RuntimeError, match="graph close failed"):
        await client.aclose()
    assert scholix_closed
