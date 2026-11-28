"""Plain DOI resolution: the resolver's 302 and its ``Location`` header."""

import pytest
from bibliofabric.exceptions import ConfigurationError, NotFoundError

from ..conftest import load_text


def last_request(httpx_mock):
    return httpx_mock.get_requests()[-1]


async def test_resolve_returns_the_redirect(client, httpx_mock):
    httpx_mock.add_response(
        status_code=302,
        headers={"Location": "https://www.nature.com/articles/nature12373"},
        text=load_text("redirect_crossref.html").replace(
            "https://api.crossref.org/v1/works/10.1038%2Fnature12373/transform",
            "https://www.nature.com/articles/nature12373",
        ),
    )
    response = await client.resolve("10.1038/nature12373")
    assert response.status_code == 302
    assert response.headers["location"] == "https://www.nature.com/articles/nature12373"
    assert b"Handle Redirect" in response.content
    request = last_request(httpx_mock)
    assert request.method == "GET"
    assert request.url.path == "/10.1038/nature12373"
    assert request.headers["accept"] == "text/html"
    assert len(httpx_mock.get_requests()) == 1


async def test_resolve_accepts_doi_urls_and_encodes_the_path(client, httpx_mock):
    httpx_mock.add_response(status_code=302, headers={"Location": "https://a.example/"})
    await client.resolve("https://doi.org/10.1000/res%23test")
    assert last_request(httpx_mock).url.raw_path == b"/10.1000/res%23test"


async def test_resolve_unknown_doi_raises_not_found(client, httpx_mock):
    httpx_mock.add_response(
        text="<!DOCTYPE html><html><title>Error: DOI Not Found</title></html>",
        status_code=404,
        headers={"content-type": "text/html"},
    )
    with pytest.raises(NotFoundError):
        await client.resolve("10.9999/nope")


async def test_resolve_rejects_a_malformed_doi_before_sending(client, httpx_mock):
    with pytest.raises(ConfigurationError, match="Not a DOI name"):
        await client.resolve("nonsense")
    assert not httpx_mock.get_requests()
