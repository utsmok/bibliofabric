"""Credential wiring: what each credential form puts on the wire."""

from bibliofabric.auth import StaticTokenAuth
from stavrophora import StavrophoraClient, StavrophoraSettings, get_settings

from .conftest import works_envelope

EMPTY = works_envelope([])


def settings(**overrides) -> StavrophoraSettings:
    # `_env_file=None` keeps a developer's `.env` out of the offline suite.
    return StavrophoraSettings(
        _env_file=None, max_requests_per_second=None, **overrides
    )


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
    assert StavrophoraSettings().rate_limits == {
        "single": 10.0,
        "list": 3.0,
        "datacitations": 3.0,
    }
    assert StavrophoraSettings(max_requests_per_second=None).rate_limits == {}
    assert StavrophoraSettings(max_requests_per_second=5.0).rate_limits == {}
    custom = StavrophoraSettings(
        max_requests_per_second=5.0, rate_limits={"single": 20.0, "list": None}
    )
    assert custom.rate_limits == {"single": 20.0, "list": None}


def _clear_stavrophora_env(monkeypatch, tmp_path) -> None:
    for var in (
        "STAVROPHORA_MAILTO",
        "STAVROPHORA_PLUS_TOKEN",
        "STAVROPHORA_RATE_LIMITS",
        "STAVROPHORA_MAX_CONCURRENCY",
        "STAVROPHORA_MAX_REQUESTS_PER_SECOND",
    ):
        monkeypatch.delenv(var, raising=False)
    get_settings.cache_clear()
    monkeypatch.chdir(tmp_path)  # no `.env` in an empty directory


def test_pool_default_rate_limits(monkeypatch, tmp_path):
    _clear_stavrophora_env(monkeypatch, tmp_path)

    public = StavrophoraClient()
    assert public.settings.rate_limits == {
        "single": 5.0,
        "list": 1.0,
        "datacitations": 3.0,
    }
    assert public.settings.max_concurrency == 1

    polite = StavrophoraClient(mailto="polite@example.org")
    assert polite.settings.rate_limits == {
        "single": 10.0,
        "list": 3.0,
        "datacitations": 3.0,
    }
    assert polite.settings.max_concurrency == 3

    plus = StavrophoraClient(plus_token="plus-key-1")
    assert plus.settings.rate_limits == {
        "single": 50.0,
        "list": 50.0,
        "datacitations": 3.0,
    }
    assert plus.settings.max_concurrency == 10

    plus_with_mailto = StavrophoraClient(
        mailto="polite@example.org", plus_token="plus-key-1"
    )
    assert plus_with_mailto.settings.rate_limits == plus.settings.rate_limits
    assert plus_with_mailto.settings.max_concurrency == 10


def test_explicit_rate_limits_and_concurrency_are_not_overridden(monkeypatch, tmp_path):
    _clear_stavrophora_env(monkeypatch, tmp_path)

    explicit = StavrophoraClient(
        plus_token="plus-key-1",
        settings=StavrophoraSettings(
            rate_limits={"single": 20.0, "list": 5.0},
            max_concurrency=4,
        ),
    )
    assert explicit.settings.rate_limits == {"single": 20.0, "list": 5.0}
    assert explicit.settings.max_concurrency == 4

    uniform = StavrophoraClient(
        mailto="polite@example.org",
        settings=StavrophoraSettings(max_requests_per_second=2.5),
    )
    assert uniform.settings.rate_limits == {}
    assert uniform.settings.max_requests_per_second == 2.5
    assert uniform.settings.max_concurrency == 3

    unthrottled = StavrophoraClient(
        settings=StavrophoraSettings(max_requests_per_second=None, max_concurrency=8)
    )
    assert unthrottled.settings.rate_limits == {}
    assert unthrottled.settings.max_concurrency == 8


async def test_on_response_tracks_crossref_rate_limit_headers(httpx_mock):
    httpx_mock.add_response(
        json=EMPTY,
        headers={
            "x-api-pool": "polite-array",
            "x-rate-limit-limit": "3",
            "x-rate-limit-interval": "1s",
            "x-concurrency-limit": "3",
            "x-unrelated-header": "ignored",
        },
    )
    httpx_mock.add_response(json=EMPTY)

    async with StavrophoraClient(
        settings=settings(mailto="tester@example.org")
    ) as client:
        assert client.last_pool is None
        assert client.last_rate_limit_headers == {}

        await client.works.search()
        assert client.last_pool == "polite-array"
        assert client.last_rate_limit_headers == {
            "x-api-pool": "polite-array",
            "x-rate-limit-limit": "3",
            "x-rate-limit-interval": "1s",
            "x-concurrency-limit": "3",
        }

        snapshot = client.last_rate_limit_headers
        snapshot["x-api-pool"] = "mutated"
        assert client.last_rate_limit_headers["x-api-pool"] == "polite-array"

        await client.works.search()
        assert client.last_pool is None
        assert client.last_rate_limit_headers == {}
