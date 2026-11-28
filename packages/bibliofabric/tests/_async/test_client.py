"""Consumer-visible behavior of BaseApiClient: error mapping, retries, JSON."""

import base64
import logging
import time
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from email.utils import format_datetime
from typing import Any, cast
from urllib.parse import parse_qs

import httpx
import pytest
from bibliofabric import BaseApiClient, BasicAuth, RefreshTokenAuth, validate_model
from bibliofabric._async import _concurrency
from bibliofabric.auth import (
    ClientCredentialsAuth,
    HeaderAuth,
    NoAuth,
    QueryParameterAuth,
    StaticTokenAuth,
)
from bibliofabric.exceptions import (
    APIError,
    AuthError,
    ConfigurationError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)

from .conftest import BASE_URL, FakeSettings, FakeUnwrapper, Widget, Widgets


class _Veto429Client(BaseApiClient):
    def is_retryable(self, response: httpx.Response) -> bool:
        return response.status_code != 429 and super().is_retryable(response)


async def test_error_status_mapping(httpx_mock, make_client):
    cases = [
        ("/s404", 404, NotFoundError),
        ("/s429", 429, RateLimitError),
        ("/s401", 401, AuthError),
        ("/s403", 403, AuthError),
        ("/s500", 500, APIError),
    ]
    for path, status, _ in cases:
        httpx_mock.add_response(url=f"{BASE_URL}{path}", status_code=status, json={})
    client = make_client(settings=FakeSettings(max_retries=0))
    for path, status, exception in cases:
        with pytest.raises(exception) as excinfo:
            await client.request("GET", path.lstrip("/"))
        assert excinfo.value.status_code == status
        assert excinfo.value.request is not None
        assert excinfo.value.response is not None


async def test_error_body_exposed_and_formatted_on_vetoed_429(httpx_mock):
    httpx_mock.add_response(
        url=f"{BASE_URL}/budget",
        status_code=429,
        headers={"Retry-After": "12"},
        json={"reason": "daily_budget", "message": "Daily budget exhausted"},
    )
    client = _Veto429Client(
        base_url=BASE_URL,
        settings=FakeSettings(max_retries=3),
        unwrapper=FakeUnwrapper(),
    )
    try:
        with pytest.raises(RateLimitError) as excinfo:
            await client.request("GET", "budget")
    finally:
        await client.aclose()
    assert excinfo.value.body == {
        "reason": "daily_budget",
        "message": "Daily budget exhausted",
    }
    assert excinfo.value.retry_after == 12.0
    assert "reason=daily_budget" in str(excinfo.value)
    assert "Daily budget exhausted" in str(excinfo.value)


async def test_auth_error_exposes_json_body(httpx_mock, make_client):
    httpx_mock.add_response(
        url=f"{BASE_URL}/secret",
        status_code=401,
        json={"error": "invalid_api_key", "message": "API key rejected"},
    )
    client = make_client(settings=FakeSettings(max_retries=0))
    with pytest.raises(AuthError) as excinfo:
        await client.request("GET", "secret")
    assert excinfo.value.body == {
        "error": "invalid_api_key",
        "message": "API key rejected",
    }
    assert "invalid_api_key" in str(excinfo.value)


async def test_error_body_none_for_plain_text(httpx_mock, make_client):
    httpx_mock.add_response(url=f"{BASE_URL}/text", status_code=500, text="oops")
    client = make_client(settings=FakeSettings(max_retries=0))
    with pytest.raises(APIError) as excinfo:
        await client.request("GET", "text")
    assert excinfo.value.body is None
    assert "oops" in str(excinfo.value)


async def test_error_str_handles_response_without_request():
    response = httpx.Response(404, text="not here")
    error = APIError("Missing item", response=response)
    assert error.request is None
    assert error.status_code == 404
    rendered = str(error)
    assert "status: 404" in rendered
    assert "not here" in rendered


async def test_404_from_get(httpx_mock, make_client):
    httpx_mock.add_response(
        url=f"{BASE_URL}/works/10.1234%2Fxyz", status_code=404, json={}
    )
    client = make_client(settings=FakeSettings(max_retries=0))
    works = Widgets(client)
    with pytest.raises(NotFoundError):
        await works.get("10.1234/xyz")


async def test_get_returns_model(httpx_mock, make_client):
    httpx_mock.add_response(url=f"{BASE_URL}/works/w1", json={"id": "w1", "title": "T"})
    client = make_client()
    works = Widgets(client)
    widget = await works.get("w1")
    assert isinstance(widget, Widget)
    assert widget.title == "T"


async def test_retry_after_header_honored(httpx_mock, make_client):
    httpx_mock.add_response(
        url=f"{BASE_URL}/works",
        status_code=429,
        headers={"Retry-After": "0.1"},
        json={},
    )
    httpx_mock.add_response(url=f"{BASE_URL}/works", json={"results": [], "total": 0})
    client = make_client(settings=FakeSettings(max_retries=2))
    started = time.monotonic()
    response = await client.request("GET", "works")
    assert response.status_code == 200
    assert time.monotonic() - started >= 0.08


async def test_retry_after_http_date_capped(httpx_mock, make_client):
    future = datetime.now(UTC) + timedelta(seconds=60)
    httpx_mock.add_response(
        url=f"{BASE_URL}/dated",
        status_code=503,
        headers={"Retry-After": format_datetime(future, usegmt=True)},
        json={},
    )
    httpx_mock.add_response(url=f"{BASE_URL}/dated", json={"ok": True})
    client = make_client(settings=FakeSettings(max_retries=1, max_retry_wait=0.05))
    started = time.monotonic()
    response = await client.request("GET", "dated")
    assert response.status_code == 200
    assert time.monotonic() - started < 1.0


async def test_retry_gives_up_after_max_retries(httpx_mock, make_client):
    for _ in range(3):
        httpx_mock.add_response(
            url=f"{BASE_URL}/works",
            status_code=503,
            headers={"Retry-After": "0"},
            json={},
        )
    client = make_client(settings=FakeSettings(max_retries=2))
    with pytest.raises(APIError) as excinfo:
        await client.request("GET", "works")
    assert excinfo.value.response is not None
    assert excinfo.value.response.status_code == 503
    assert len(httpx_mock.get_requests()) == 3


async def test_429_not_retried_when_vetoed(httpx_mock):
    httpx_mock.add_response(
        url=f"{BASE_URL}/works", status_code=429, json={"reason": "daily_budget"}
    )

    client = _Veto429Client(
        base_url=BASE_URL,
        settings=FakeSettings(max_retries=3),
        unwrapper=FakeUnwrapper(),
    )
    try:
        with pytest.raises(RateLimitError) as excinfo:
            await client.request("GET", "works")
    finally:
        await client.aclose()
    assert excinfo.value.body == {"reason": "daily_budget"}
    assert len(httpx_mock.get_requests()) == 1


async def test_network_and_timeout_errors_and_redaction(httpx_mock, make_client):
    httpx_mock.add_exception(
        httpx.ConnectError("boom https://fake.test/api/down?api_key=supersecret"),
        url=f"{BASE_URL}/down?api_key=supersecret",
    )
    httpx_mock.add_exception(httpx.ReadTimeout("t"), url=f"{BASE_URL}/slow")
    client = make_client(settings=FakeSettings(max_retries=0))
    with pytest.raises(NetworkError) as net_exc:
        await client.request("GET", "down", params={"api_key": "supersecret"})
    assert "supersecret" not in net_exc.value.message
    assert "supersecret" not in str(net_exc.value)
    with pytest.raises(TimeoutError) as excinfo:
        await client.request("GET", "slow")
    assert isinstance(excinfo.value, TimeoutError)


async def test_get_json_and_invalid_json_raises_api_error(httpx_mock, make_client):
    httpx_mock.add_response(url=f"{BASE_URL}/works", json={"results": [1]})
    httpx_mock.add_response(url=f"{BASE_URL}/html", text="<html>maintenance</html>")
    client = make_client()
    assert await client.get_json("works", headers={"X-Custom": "1"}) == {"results": [1]}
    assert httpx_mock.get_requests()[0].headers["X-Custom"] == "1"
    with pytest.raises(APIError) as excinfo:
        await client.get_json("html")
    assert excinfo.value.status_code == 200
    assert "invalid JSON" in str(excinfo.value)


async def test_injected_http_client_without_base_url_and_lifecycle(httpx_mock):
    httpx_mock.add_response(url=f"{BASE_URL}/ping", json={"ok": True})
    shared = httpx.AsyncClient()
    client = BaseApiClient(
        base_url=BASE_URL,
        settings=FakeSettings(user_agent="custom-agent/2.0"),
        unwrapper=FakeUnwrapper(),
        http_client=shared,
    )
    assert client.base_url == BASE_URL
    async with client:
        assert await client.get_json("ping") == {"ok": True}
    sent = httpx_mock.get_requests()[0]
    assert str(sent.url) == f"{BASE_URL}/ping"
    assert sent.headers["User-Agent"] == "custom-agent/2.0"
    # Caller-owned client must remain open after aclose().
    assert not shared.is_closed
    await shared.aclose()


async def test_owned_http_client_closed_by_context_manager(httpx_mock):
    httpx_mock.add_response(url=f"{BASE_URL}/ping", json={"ok": True})
    async with BaseApiClient(
        base_url=BASE_URL,
        settings=FakeSettings(),
        unwrapper=FakeUnwrapper(),
    ) as client:
        await client.get_json("ping")
        internal = client._http_client
    assert internal.is_closed


async def test_request_supports_data_content_and_timeout(httpx_mock, make_client):
    httpx_mock.add_response(url=f"{BASE_URL}/form", method="POST", json={"ok": True})
    httpx_mock.add_response(url=f"{BASE_URL}/raw", method="POST", json={"ok": True})
    client = make_client()
    await client.request("POST", "form", data={"a": "1"}, timeout=5.0)
    await client.request("POST", "raw", content=b"bytes", timeout=httpx.Timeout(5.0))
    requests = httpx_mock.get_requests()
    assert requests[0].content == b"a=1"
    assert requests[1].content == b"bytes"


async def test_client_credentials_token_fetch_and_refresh(httpx_mock, make_client):
    client = make_client(
        auth=ClientCredentialsAuth(
            "id", "secret", "https://auth.test/token", user_agent="myclient/1.0"
        )
    )
    httpx_mock.add_response(
        url="https://auth.test/token", json={"access_token": "tok1", "expires_in": 3600}
    )
    httpx_mock.add_response(url=f"{BASE_URL}/works", json={"results": []})
    await client.request("GET", "works")
    token_requests = [
        r for r in httpx_mock.get_requests() if str(r.url) == "https://auth.test/token"
    ]
    assert len(token_requests) == 1
    assert token_requests[0].headers["User-Agent"] == "myclient/1.0"
    sent = [r for r in httpx_mock.get_requests() if str(r.url).startswith(BASE_URL)]
    assert sent[0].headers["Authorization"] == "Bearer tok1"

    # Force expiry: the next request must fetch a fresh token.
    auth = client._auth
    assert isinstance(auth, ClientCredentialsAuth)
    auth._token_expires_at = time.monotonic() - 1
    httpx_mock.add_response(
        url="https://auth.test/token", json={"access_token": "tok2", "expires_in": 3600}
    )
    httpx_mock.add_response(url=f"{BASE_URL}/works", json={"results": []})
    await client.request("GET", "works")
    token_requests = [
        r for r in httpx_mock.get_requests() if str(r.url) == "https://auth.test/token"
    ]
    assert len(token_requests) == 2
    sent = [r for r in httpx_mock.get_requests() if str(r.url).startswith(BASE_URL)]
    assert sent[-1].headers["Authorization"] == "Bearer tok2"
    await client.aclose()


async def test_client_credentials_error_and_expiry_edge_cases(httpx_mock, make_client):
    # Non-JSON 200 raises AuthError (not JSONDecodeError).
    httpx_mock.add_response(url="https://auth.test/bad-json", text="<html>err</html>")
    bad_json_client = make_client(
        auth=ClientCredentialsAuth("id", "secret", "https://auth.test/bad-json")
    )
    with pytest.raises(AuthError):
        await bad_json_client.request("GET", "works")
    await bad_json_client.aclose()

    # HTTP 401 from token endpoint attaches response & body to AuthError.
    httpx_mock.add_response(
        url="https://auth.test/denied",
        status_code=401,
        json={"error": "invalid_client"},
    )
    denied_client = make_client(
        auth=ClientCredentialsAuth("id", "secret", "https://auth.test/denied")
    )
    with pytest.raises(AuthError) as excinfo:
        await denied_client.request("GET", "works")
    assert excinfo.value.status_code == 401
    assert excinfo.value.body == {"error": "invalid_client"}
    await denied_client.aclose()

    # expires_in=0 means expired immediately; short expires_in=10 caches with clamped buffer.
    httpx_mock.add_response(
        url="https://auth.test/short", json={"access_token": "t0", "expires_in": 0}
    )
    httpx_mock.add_response(
        url="https://auth.test/short", json={"access_token": "t1", "expires_in": 10}
    )
    httpx_mock.add_response(url=f"{BASE_URL}/w", json={}, is_reusable=True)
    short_client = make_client(
        auth=ClientCredentialsAuth("id", "secret", "https://auth.test/short")
    )
    await short_client.request("GET", "w")
    await short_client.request("GET", "w")
    await short_client.request("GET", "w")
    token_posts = [
        r for r in httpx_mock.get_requests() if str(r.url) == "https://auth.test/short"
    ]
    assert len(token_posts) == 2
    await short_client.aclose()


async def test_client_credentials_concurrent_refresh_runs_once(httpx_mock, make_client):
    httpx_mock.add_response(
        url="https://auth.test/once",
        json={"access_token": "shared", "expires_in": 3600},
    )
    httpx_mock.add_response(url=f"{BASE_URL}/w", json={}, is_reusable=True)
    client = make_client(
        auth=ClientCredentialsAuth("id", "secret", "https://auth.test/once")
    )
    await _concurrency.run_bounded(
        lambda _: client.request("GET", "w"), [1, 2, 3, 4], concurrency=4
    )
    token_posts = [
        r for r in httpx_mock.get_requests() if str(r.url) == "https://auth.test/once"
    ]
    assert len(token_posts) == 1
    await client.aclose()


def test_client_credentials_requires_configuration():
    with pytest.raises(ConfigurationError):
        ClientCredentialsAuth("", "secret", "https://auth.test/token")


async def test_query_parameter_auth(httpx_mock, make_client):
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?api_key=secret", json={"results": []}
    )
    client = make_client(auth=QueryParameterAuth("api_key", "secret"))
    await client.request("GET", "works")


async def test_header_auth(httpx_mock, make_client):
    httpx_mock.add_response(url=f"{BASE_URL}/works", json={"results": []})
    client = make_client(auth=HeaderAuth("Crossref-Plus-API-Token", "tok"))
    await client.request("GET", "works")
    sent = httpx_mock.get_requests()
    assert sent[0].headers["Crossref-Plus-API-Token"] == "tok"


async def test_static_token_auth_bearer():
    auth = StaticTokenAuth("tok")
    request = httpx.Request("GET", "https://x.test/api")
    await auth.async_authenticate(request)
    assert request.headers["Authorization"] == "Bearer tok"
    with pytest.raises(ConfigurationError):
        StaticTokenAuth("")


def test_validate_model_helper():
    widget = validate_model(Widget, {"id": "w1", "title": "Ok"})
    assert widget.id == "w1"
    with pytest.raises(ValidationError) as excinfo:
        validate_model(Widget, {"title": 123})
    assert excinfo.value.raw == {"title": 123}
    assert excinfo.value.model_name == "Widget"


async def test_idempotent_retry_policy_and_retry_override(httpx_mock, make_client):
    client = make_client(settings=FakeSettings(max_retries=2, max_retry_wait=0.0))

    # Non-idempotent POST and PATCH do not retry by default.
    httpx_mock.add_response(url=f"{BASE_URL}/items", method="POST", status_code=503)
    with pytest.raises(APIError):
        await client.request("POST", "items", json={"x": 1})
    assert len(httpx_mock.get_requests(method="POST")) == 1

    httpx_mock.add_response(url=f"{BASE_URL}/items/1", method="PATCH", status_code=503)
    with pytest.raises(APIError):
        await client.request("PATCH", "items/1", json={"x": 2})
    assert len(httpx_mock.get_requests(method="PATCH")) == 1

    # Explicit retry=True enables retries on POST (e.g. read-only POST batch APIs).
    httpx_mock.add_response(
        url=f"{BASE_URL}/batch",
        method="POST",
        status_code=503,
        headers={"Retry-After": "0"},
    )
    httpx_mock.add_response(
        url=f"{BASE_URL}/batch", method="POST", json={"results": []}
    )
    response = await client.request("POST", "batch", json={"ids": ["1"]}, retry=True)
    assert response.status_code == 200
    assert len(httpx_mock.get_requests(url=f"{BASE_URL}/batch")) == 2

    # Idempotent PUT/DELETE retry by default.
    httpx_mock.add_response(
        url=f"{BASE_URL}/items/1",
        method="PUT",
        status_code=503,
        headers={"Retry-After": "0"},
    )
    httpx_mock.add_response(url=f"{BASE_URL}/items/1", method="PUT", json={"ok": True})
    assert (await client.request("PUT", "items/1", json={"x": 1})).status_code == 200
    assert len(httpx_mock.get_requests(method="PUT")) == 2

    # Explicit retry=False disables retries even on GET.
    httpx_mock.add_response(url=f"{BASE_URL}/noretry", method="GET", status_code=503)
    with pytest.raises(APIError):
        await client.request("GET", "noretry", retry=False)
    assert len(httpx_mock.get_requests(url=f"{BASE_URL}/noretry")) == 1


async def test_owned_http_client_limits_redirects_and_connect_timeout(monkeypatch):
    captured: dict[str, Any] = {}
    orig_limits = httpx.Limits

    def spy_limits(*args: Any, **kwargs: Any) -> httpx.Limits:
        captured["limits_kwargs"] = kwargs
        return orig_limits(*args, **kwargs)

    monkeypatch.setattr(httpx, "Limits", spy_limits)

    client_default = BaseApiClient(
        base_url=BASE_URL,
        settings=FakeSettings(max_concurrency=4),
        unwrapper=FakeUnwrapper(),
    )
    try:
        assert client_default._http_client.follow_redirects is False
        assert captured["limits_kwargs"] == {
            "max_connections": 20,
            "max_keepalive_connections": 10,
        }
        assert client_default._http_client.timeout == httpx.Timeout(30.0)
    finally:
        await client_default.aclose()

    client_custom = BaseApiClient(
        base_url=BASE_URL,
        settings=FakeSettings(
            timeout=45.0,
            connect_timeout=5.0,
            follow_redirects=True,
            max_concurrency=25,
        ),
        unwrapper=FakeUnwrapper(),
    )
    try:
        assert client_custom._http_client.follow_redirects is True
        assert captured["limits_kwargs"] == {
            "max_connections": 50,
            "max_keepalive_connections": 25,
        }
        assert client_custom._http_client.timeout == httpx.Timeout(45.0, connect=5.0)
    finally:
        await client_custom.aclose()


async def test_basic_auth_header_and_validation(httpx_mock, make_client):
    httpx_mock.add_response(url=f"{BASE_URL}/works", json={"results": []})
    auth = BasicAuth("repo_user", "s3cr3t")
    assert auth.redacted_headers == frozenset({"authorization"})
    assert auth.redacted_query_params == frozenset()
    client = make_client(auth=auth)
    await client.request("GET", "works")
    expected = base64.b64encode(b"repo_user:s3cr3t").decode("ascii")
    assert httpx_mock.get_requests()[0].headers["Authorization"] == f"Basic {expected}"
    await client.aclose()

    with pytest.raises(ConfigurationError):
        BasicAuth("", "pw")
    with pytest.raises(ConfigurationError):
        BasicAuth("user", "")


async def test_client_credentials_scope_post_method_http_client_and_invalidate(
    httpx_mock, make_client
):
    shared_http = httpx.AsyncClient()
    auth = ClientCredentialsAuth(
        "cid",
        "csec",
        "https://auth.test/orcid",
        scope="/read-public",
        token_auth_method="post",
        timeout=12.0,
        http_client=shared_http,
    )
    httpx_mock.add_response(
        url="https://auth.test/orcid",
        json={"access_token": "tok_a", "expires_in": 3600},
    )
    httpx_mock.add_response(url=f"{BASE_URL}/works", json={"results": []})
    client = make_client(auth=auth)
    await client.request("GET", "works")

    token_req = [
        r for r in httpx_mock.get_requests() if str(r.url) == "https://auth.test/orcid"
    ][0]
    assert "Authorization" not in token_req.headers
    form = parse_qs(token_req.content.decode())
    assert form == {
        "grant_type": ["client_credentials"],
        "scope": ["/read-public"],
        "client_id": ["cid"],
        "client_secret": ["csec"],
    }

    # invalidate_token forces a fresh fetch on the next request.
    auth.invalidate_token()
    httpx_mock.add_response(
        url="https://auth.test/orcid",
        json={"access_token": "tok_b", "expires_in": 3600},
    )
    httpx_mock.add_response(url=f"{BASE_URL}/works", json={"results": []})
    await client.request("GET", "works")
    api_reqs = [r for r in httpx_mock.get_requests() if str(r.url).startswith(BASE_URL)]
    assert api_reqs[-1].headers["Authorization"] == "Bearer tok_b"

    # Caller-owned http_client must remain open after aclose().
    await client.aclose()
    assert not shared_http.is_closed
    await shared_http.aclose()

    with pytest.raises(ConfigurationError):
        ClientCredentialsAuth(
            "id",
            "sec",
            "https://auth.test/t",
            token_auth_method=cast(Any, "invalid"),
        )


def test_client_credentials_invalid_method_and_timeout():
    with pytest.raises(ConfigurationError):
        ClientCredentialsAuth("id", "sec", "https://auth.test/t", timeout=0)
    with pytest.raises(ConfigurationError):
        ClientCredentialsAuth("id", "sec", "https://auth.test/t", timeout=float("inf"))


async def test_refresh_token_auth_lifecycle_rotation_and_errors(
    httpx_mock, make_client
):
    shared_http = httpx.AsyncClient()
    auth = RefreshTokenAuth(
        "https://auth.test/refresh",
        "rt_initial",
        client_id="cid",
        client_secret="csec",
        scope="read",
        timeout=20.0,
        http_client=shared_http,
    )
    httpx_mock.add_response(
        url="https://auth.test/refresh",
        json={
            "access_token": "at_1",
            "expires_in": 3600,
            "refresh_token": "rt_rotated",
        },
    )
    httpx_mock.add_response(
        url=f"{BASE_URL}/works", json={"results": []}, is_reusable=True
    )
    client = make_client(auth=auth)
    await client.request("GET", "works")
    await client.request("GET", "works")  # cached

    refresh_reqs = [
        r
        for r in httpx_mock.get_requests()
        if str(r.url) == "https://auth.test/refresh"
    ]
    assert len(refresh_reqs) == 1
    assert parse_qs(refresh_reqs[0].content.decode()) == {
        "grant_type": ["refresh_token"],
        "refresh_token": ["rt_initial"],
        "client_id": ["cid"],
        "client_secret": ["csec"],
        "scope": ["read"],
    }

    # After invalidation, uses the rotated refresh token.
    auth.invalidate_token()
    httpx_mock.add_response(
        url="https://auth.test/refresh",
        json={"access_token": "at_2", "expires_in": 3600},
    )
    await client.request("GET", "works")
    refresh_reqs = [
        r
        for r in httpx_mock.get_requests()
        if str(r.url) == "https://auth.test/refresh"
    ]
    assert len(refresh_reqs) == 2
    assert parse_qs(refresh_reqs[1].content.decode())["refresh_token"] == ["rt_rotated"]

    await client.aclose()
    assert not shared_http.is_closed
    await shared_http.aclose()

    # Error wrapping: 400 from token endpoint raises AuthError with body.
    httpx_mock.add_response(
        url="https://auth.test/bad-refresh",
        status_code=400,
        json={"error": "invalid_grant"},
    )
    bad_client = make_client(
        auth=RefreshTokenAuth("https://auth.test/bad-refresh", "expired_rt")
    )
    with pytest.raises(AuthError) as excinfo:
        await bad_client.request("GET", "works")
    assert excinfo.value.body == {"error": "invalid_grant"}
    await bad_client.aclose()

    with pytest.raises(ConfigurationError):
        RefreshTokenAuth("", "rt")
    with pytest.raises(ConfigurationError):
        RefreshTokenAuth("https://auth.test/r", "")
    with pytest.raises(ConfigurationError):
        RefreshTokenAuth("https://auth.test/r", "rt", client_id="")
    with pytest.raises(ConfigurationError):
        RefreshTokenAuth("https://auth.test/r", "rt", timeout=-5)


async def test_single_retry_on_401_token_refresh(httpx_mock, make_client):
    auth = ClientCredentialsAuth("id", "sec", "https://auth.test/401")
    httpx_mock.add_response(
        url="https://auth.test/401",
        json={"access_token": "stale_tok", "expires_in": 3600},
    )
    httpx_mock.add_response(
        url="https://auth.test/401",
        json={"access_token": "fresh_tok", "expires_in": 3600},
    )
    httpx_mock.add_response(url=f"{BASE_URL}/protected", status_code=401, json={})
    httpx_mock.add_response(url=f"{BASE_URL}/protected", json={"ok": True})

    client = make_client(auth=auth, settings=FakeSettings(max_retries=0))
    response = await client.request("GET", "protected")
    assert response.status_code == 200
    api_reqs = [
        r for r in httpx_mock.get_requests() if str(r.url) == f"{BASE_URL}/protected"
    ]
    assert [r.headers["Authorization"] for r in api_reqs] == [
        "Bearer stale_tok",
        "Bearer fresh_tok",
    ]
    await client.aclose()

    # Persistent 401 only retries once and then raises AuthError.
    auth2 = ClientCredentialsAuth("id", "sec", "https://auth.test/401-fail")
    httpx_mock.add_response(
        url="https://auth.test/401-fail",
        json={"access_token": "bad1", "expires_in": 3600},
    )
    httpx_mock.add_response(
        url="https://auth.test/401-fail",
        json={"access_token": "bad2", "expires_in": 3600},
    )
    httpx_mock.add_response(
        url=f"{BASE_URL}/revoked", status_code=401, json={"error": "revoked"}
    )
    httpx_mock.add_response(
        url=f"{BASE_URL}/revoked", status_code=401, json={"error": "revoked"}
    )
    client2 = make_client(auth=auth2, settings=FakeSettings(max_retries=0))
    with pytest.raises(AuthError):
        await client2.request("GET", "revoked")
    assert len(httpx_mock.get_requests(url=f"{BASE_URL}/revoked")) == 2
    await client2.aclose()


async def test_custom_auth_redaction_in_logs_and_errors(
    httpx_mock, make_client, caplog
):
    assert NoAuth().redacted_query_params == frozenset()
    assert NoAuth().redacted_headers == frozenset()
    assert StaticTokenAuth("t").redacted_headers == frozenset({"authorization"})

    # Custom query param name not in built-in regex is redacted in logs AND errors.
    qp_auth = QueryParameterAuth("custom_cred", "ultra_secret_val")
    assert qp_auth.redacted_query_params == frozenset({"custom_cred"})
    httpx_mock.add_response(
        url=f"{BASE_URL}/secret-qp?custom_cred=ultra_secret_val",
        status_code=500,
        json={"error": "boom"},
    )
    client = make_client(auth=qp_auth, settings=FakeSettings(max_retries=0))
    with (
        caplog.at_level(logging.DEBUG, logger="bibliofabric"),
        pytest.raises(APIError) as excinfo,
    ):
        await client.request("GET", "secret-qp")
    assert "ultra_secret_val" not in str(excinfo.value)
    assert "custom_cred=***" in str(excinfo.value)
    assert "ultra_secret_val" not in caplog.text
    assert "custom_cred=***" in caplog.text

    # Custom header name not containing built-in markers is redacted in debug logs.
    caplog.clear()
    hdr_auth = HeaderAuth("X-Custom-Pass", "hdr_secret_val")
    assert hdr_auth.redacted_headers == frozenset({"x-custom-pass"})
    httpx_mock.add_response(url=f"{BASE_URL}/secret-hdr", json={"ok": True})
    client2 = make_client(auth=hdr_auth)
    with caplog.at_level(logging.DEBUG, logger="bibliofabric"):
        await client2.request("GET", "secret-hdr")
    assert "hdr_secret_val" not in caplog.text
    assert "'x-custom-pass': '***'" in caplog.text


async def test_on_response_hook_and_stream(httpx_mock):
    observed: list[tuple[int, str | None]] = []

    class _ObservingClient(BaseApiClient):
        def on_response(self, response: httpx.Response) -> None:
            observed.append(
                (response.status_code, response.headers.get("X-RateLimit-Remaining"))
            )

    httpx_mock.add_response(
        url=f"{BASE_URL}/ok",
        headers={"X-RateLimit-Remaining": "99"},
        json={"ok": True},
    )
    httpx_mock.add_response(
        url=f"{BASE_URL}/missing",
        status_code=404,
        headers={"X-RateLimit-Remaining": "98"},
        json={"error": "gone"},
    )
    httpx_mock.add_response(
        url=f"{BASE_URL}/download?v=1",
        headers={"X-RateLimit-Remaining": "97"},
        content=b"hello stream",
    )
    httpx_mock.add_response(
        url=f"{BASE_URL}/bad-stream",
        status_code=404,
        headers={"X-RateLimit-Remaining": "96"},
        json={"message": "file not found"},
    )

    client = _ObservingClient(
        base_url=BASE_URL,
        settings=FakeSettings(max_retries=0),
        unwrapper=FakeUnwrapper(),
        auth=StaticTokenAuth("tok"),
    )
    try:
        await client.request("GET", "ok")
        with pytest.raises(NotFoundError):
            await client.request("GET", "missing")

        async with client.stream("GET", "download", params={"v": "1"}) as resp:
            assert resp.request.headers["Authorization"] == "Bearer tok"
            chunks = [chunk async for chunk in resp.aiter_bytes()]
        assert b"".join(chunks) == b"hello stream"

        async def _open_bad_stream() -> None:
            async with client.stream("GET", "bad-stream"):
                pass

        with pytest.raises(NotFoundError) as excinfo:
            await _open_bad_stream()
        assert excinfo.value.body == {"message": "file not found"}
        assert "file not found" in str(excinfo.value)
    finally:
        await client.aclose()

    assert observed == [(200, "99"), (404, "98"), (200, "97"), (404, "96")]


async def test_stream_refreshes_token_once_on_401(httpx_mock, make_client):
    auth = ClientCredentialsAuth("id", "sec", "https://auth.test/stream-401")
    httpx_mock.add_response(
        url="https://auth.test/stream-401",
        json={"access_token": "old", "expires_in": 3600},
    )
    httpx_mock.add_response(
        url="https://auth.test/stream-401",
        json={"access_token": "new", "expires_in": 3600},
    )
    httpx_mock.add_response(url=f"{BASE_URL}/file", status_code=401, json={})
    httpx_mock.add_response(url=f"{BASE_URL}/file", content=b"payload")

    client = make_client(auth=auth, settings=FakeSettings(max_retries=0))
    async with client.stream("GET", "file") as resp:
        chunks = [chunk async for chunk in resp.aiter_bytes()]
    assert b"".join(chunks) == b"payload"
    await client.aclose()


class _AcceptPinnedClient(BaseApiClient):
    @property
    def default_headers(self) -> Mapping[str, str]:
        return {"Accept": "application/vnd.orcid+json"}


async def test_default_headers_sent_and_overridden_per_call(httpx_mock, make_client):
    httpx_mock.add_response(url=f"{BASE_URL}/record", json={"ok": True})
    httpx_mock.add_response(url=f"{BASE_URL}/xml", json={"ok": True})
    httpx_mock.add_response(url=f"{BASE_URL}/file", content=b"<record/>")

    client = _AcceptPinnedClient(
        base_url=BASE_URL,
        settings=FakeSettings(max_retries=0),
        unwrapper=FakeUnwrapper(),
    )
    try:
        await client.request("GET", "record")
        await client.request("GET", "xml", headers={"accept": "application/xml"})
        async with client.stream("GET", "file") as response:
            await response.aread()
    finally:
        await client.aclose()

    record, xml, streamed = httpx_mock.get_requests()
    assert record.headers["Accept"] == "application/vnd.orcid+json"
    # A per-call header replaces the default instead of duplicating it.
    assert xml.headers.get_list("accept") == ["application/xml"]
    assert streamed.headers["Accept"] == "application/vnd.orcid+json"
    assert dict(make_client().default_headers) == {}


async def test_follow_redirects_overrides_the_setting_per_call(httpx_mock, make_client):
    redirect = {"Location": f"{BASE_URL}/landing"}
    for _ in range(3):
        httpx_mock.add_response(
            url=f"{BASE_URL}/resolve", status_code=302, headers=redirect
        )
    httpx_mock.add_response(url=f"{BASE_URL}/landing", json={"landed": True})
    httpx_mock.add_response(url=f"{BASE_URL}/landing", content=b"file")

    # With the default setting (False) a call opts in to following.
    client = make_client(settings=FakeSettings(max_retries=0))
    response = await client.request("GET", "resolve")
    assert response.status_code == 302
    assert response.headers["Location"] == f"{BASE_URL}/landing"
    response = await client.request("GET", "resolve", follow_redirects=True)
    assert response.json() == {"landed": True}
    async with client.stream("GET", "resolve", follow_redirects=True) as response:
        assert await response.aread() == b"file"
    assert len(httpx_mock.get_requests()) == 5

    # With the setting on, a call opts out to read the 3xx itself.
    for _ in range(2):
        httpx_mock.add_response(
            url=f"{BASE_URL}/resolve", status_code=302, headers=redirect
        )
    httpx_mock.add_response(url=f"{BASE_URL}/landing", json={"landed": True})
    following = BaseApiClient(
        base_url=BASE_URL,
        settings=FakeSettings(max_retries=0, follow_redirects=True),
        unwrapper=FakeUnwrapper(),
    )
    try:
        response = await following.request("GET", "resolve")
        assert response.json() == {"landed": True}
        response = await following.request("GET", "resolve", follow_redirects=False)
        assert response.status_code == 302
    finally:
        await following.aclose()
