"""Credential wiring: Keycloak client-credentials flow and anonymous mode."""

from bibliofabric.auth import NoAuth

from aireloom import AireloomClient, AireloomSettings

from .conftest import TOKEN_URL, json_response, load, make_settings


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
