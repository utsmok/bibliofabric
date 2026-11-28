"""The optional API token: the bearer header and the authenticated page size."""

from zenotheca import ZenothecaClient, ZenothecaSettings

from ..conftest import RECORD_ID, load_fixture, record
from .test_request_shape import RECORD_PAYLOAD

SEARCH_PAGE = load_fixture("search_page.json")
TOKEN_SETTINGS = ZenothecaSettings(
    _env_file=None,
    api_token="secret-value",
    max_requests_per_second=1_000_000.0,
    max_concurrency=5,
    max_retries=0,
    max_retry_wait=0.05,
    timeout=5.0,
)


async def test_token_is_sent_as_a_bearer_header(httpx_mock):
    httpx_mock.add_response(json=RECORD_PAYLOAD)
    async with ZenothecaClient(settings=TOKEN_SETTINGS) as client:
        await client.records.get(RECORD_ID)
    request = httpx_mock.get_requests()[-1]
    assert request.headers["Authorization"] == "Bearer secret-value"


async def test_token_allows_the_documented_page_size(httpx_mock):
    httpx_mock.add_response(json=SEARCH_PAGE)
    async with ZenothecaClient(settings=TOKEN_SETTINGS) as client:
        assert client.records.dialect.max_page_size == 100
        await client.records.search(query="ror", page_size=100)
    request = httpx_mock.get_requests()[-1]
    assert request.url.params["size"] == "100"


async def test_no_token_sends_no_authorization_header(settings, httpx_mock):
    httpx_mock.add_response(json=record())
    async with ZenothecaClient(settings=settings) as client:
        assert client.records.dialect.max_page_size == 25
        await client.records.search(query="ror", page_size=100)
    request = httpx_mock.get_requests()[-1]
    assert "Authorization" not in request.headers
    assert request.url.params["size"] == "25"
