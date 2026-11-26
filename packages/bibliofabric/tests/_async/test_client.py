"""Consumer-visible behavior of BaseApiClient: error mapping, retries, JSON."""

import time

import httpx
import pytest
from bibliofabric.auth import (
    ClientCredentialsAuth,
    HeaderAuth,
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
)

from .conftest import BASE_URL, FakeSettings, Widget, Widgets


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
    for path, _, exception in cases:
        with pytest.raises(exception):
            await client.request("GET", path.lstrip("/"))


async def test_error_body_exposed_on_vetoed_429(httpx_mock, make_client):
    httpx_mock.add_response(
        url=f"{BASE_URL}/budget", status_code=429, json={"reason": "daily_budget"}
    )
    client = make_client(settings=FakeSettings(max_retries=3))
    client.is_retryable = lambda response: response.status_code != 429  # type: ignore[method-assign]
    with pytest.raises(RateLimitError) as excinfo:
        await client.request("GET", "budget")
    assert excinfo.value.body == {"reason": "daily_budget"}


async def test_error_body_none_for_plain_text(httpx_mock, make_client):
    httpx_mock.add_response(url=f"{BASE_URL}/text", status_code=500, text="oops")
    client = make_client(settings=FakeSettings(max_retries=0))
    with pytest.raises(APIError) as excinfo:
        await client.request("GET", "text")
    assert excinfo.value.body is None


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
        headers={"Retry-After": "1"},
        json={},
    )
    httpx_mock.add_response(url=f"{BASE_URL}/works", json={"results": [], "total": 0})
    client = make_client(settings=FakeSettings(max_retries=2))
    started = time.monotonic()
    response = await client.request("GET", "works")
    assert response.status_code == 200
    assert time.monotonic() - started >= 1.0


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


async def test_429_not_retried_when_vetoed(httpx_mock, make_client):
    httpx_mock.add_response(
        url=f"{BASE_URL}/works", status_code=429, json={"reason": "daily_budget"}
    )

    client = make_client(settings=FakeSettings(max_retries=3))
    client.is_retryable = lambda response: response.status_code != 429  # type: ignore[method-assign]
    with pytest.raises(RateLimitError) as excinfo:
        await client.request("GET", "works")
    assert excinfo.value.body == {"reason": "daily_budget"}
    assert len(httpx_mock.get_requests()) == 1


async def test_network_and_timeout_errors(httpx_mock, make_client):
    httpx_mock.add_exception(httpx.ConnectError("boom"), url=f"{BASE_URL}/down")
    httpx_mock.add_exception(httpx.ReadTimeout("t"), url=f"{BASE_URL}/slow")
    client = make_client(settings=FakeSettings(max_retries=0))
    with pytest.raises(NetworkError):
        await client.request("GET", "down")
    with pytest.raises(TimeoutError) as excinfo:
        await client.request("GET", "slow")
    assert isinstance(excinfo.value, TimeoutError)


async def test_get_json(httpx_mock, make_client):
    httpx_mock.add_response(url=f"{BASE_URL}/works", json={"results": [1]})
    client = make_client()
    assert await client.get_json("works") == {"results": [1]}


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
    auth._token_expires_at = time.time() - 1
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
