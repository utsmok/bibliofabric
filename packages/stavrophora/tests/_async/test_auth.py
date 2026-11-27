"""Credential wiring: what each credential form puts on the wire."""

from bibliofabric.auth import StaticTokenAuth
from stavrophora import StavrophoraClient, StavrophoraSettings

from .conftest import works_envelope

EMPTY = works_envelope([])


def settings(**overrides) -> StavrophoraSettings:
    return StavrophoraSettings(max_requests_per_second=None, **overrides)


async def single_request(httpx_mock, client):
    httpx_mock.add_response(json=EMPTY)
    await client.works.search()
    return httpx_mock.get_requests()[0]


async def test_mailto_is_sent_as_query_parameter(httpx_mock):
    client = StavrophoraClient(settings=settings(mailto="tester@example.org"))
    async with client:
        request = await single_request(httpx_mock, client)
    assert request.url.params["mailto"] == "tester@example.org"
    assert "crossref-api-key" not in request.headers


async def test_plus_token_is_sent_as_bearer_header(httpx_mock):
    client = StavrophoraClient(settings=settings(plus_token="plus-key-1"))
    async with client:
        request = await single_request(httpx_mock, client)
    assert request.headers["crossref-api-key"] == "Bearer plus-key-1"
    assert "mailto" not in request.url.params


async def test_explicit_auth_strategy_wins_over_credentials(httpx_mock):
    client = StavrophoraClient(
        settings=settings(mailto="tester@example.org", plus_token="plus-key-1"),
        auth_strategy=StaticTokenAuth("other-token"),
    )
    async with client:
        request = await single_request(httpx_mock, client)
    assert request.headers["Authorization"] == "Bearer other-token"
    assert "crossref-api-key" not in request.headers
    assert "mailto" not in request.url.params


async def test_no_credentials_sends_no_auth(httpx_mock, monkeypatch):
    monkeypatch.delenv("STAVROPHORA_MAILTO", raising=False)
    monkeypatch.delenv("STAVROPHORA_PLUS_TOKEN", raising=False)
    client = StavrophoraClient(settings=settings())
    async with client:
        request = await single_request(httpx_mock, client)
    assert "mailto" not in request.url.params
    assert "crossref-api-key" not in request.headers
    assert "Authorization" not in request.headers


def test_env_mapping(monkeypatch):
    monkeypatch.setenv("STAVROPHORA_MAILTO", "env@example.org")
    monkeypatch.setenv("STAVROPHORA_PLUS_TOKEN", "env-token")
    loaded = StavrophoraSettings()
    assert loaded.mailto == "env@example.org"
    assert loaded.plus_token == "env-token"


async def test_mailto_kwarg_rides_user_agent(httpx_mock):
    client = StavrophoraClient(settings=settings(), mailto="kwarg@example.org")
    async with client:
        request = await single_request(httpx_mock, client)
    assert request.url.params["mailto"] == "kwarg@example.org"
    assert "mailto:kwarg@example.org" in request.headers["user-agent"]


async def test_plus_token_keeps_kwarg_mailto_in_user_agent(httpx_mock):
    client = StavrophoraClient(
        settings=settings(), mailto="kwarg@example.org", plus_token="plus-key-1"
    )
    async with client:
        request = await single_request(httpx_mock, client)
    assert request.headers["crossref-api-key"] == "Bearer plus-key-1"
    assert "mailto" not in request.url.params
    assert "mailto:kwarg@example.org" in request.headers["user-agent"]


def test_max_requests_per_second_overrides_default_rate_limits():
    assert StavrophoraSettings().rate_limits == {"single": 10.0, "list": 3.0}
    assert StavrophoraSettings(max_requests_per_second=None).rate_limits == {}
    assert StavrophoraSettings(max_requests_per_second=5.0).rate_limits == {}
    custom = StavrophoraSettings(
        max_requests_per_second=5.0, rate_limits={"single": 20.0, "list": None}
    )
    assert custom.rate_limits == {"single": 20.0, "list": None}
