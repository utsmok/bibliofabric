"""Content negotiation: Accept headers, typed JSON, text representations."""

import pytest
from hodoi import (
    BIBTEX,
    CSL_JSON,
    DATACITE_JSON,
    RIS,
    SCHEMAORG_JSONLD,
    ConfigurationError,
    CslItem,
    DataciteRecord,
    SchemaOrgThing,
)

from ..conftest import load_fixture

CSL = load_fixture("cn_crossref_csl.json")
DATACITE = load_fixture("cn_datacite_datacite.json")


def last_request(httpx_mock):
    return httpx_mock.get_requests()[-1]


async def test_content_parses_csl_json(client, httpx_mock):
    httpx_mock.add_response(json=CSL)
    item = await client.content("10.1038/nature12373", CSL_JSON)
    assert isinstance(item, CslItem)
    assert item.DOI == "10.1038/nature12373"
    assert item.title == "Nanometre-scale thermometry in a living cell"
    assert item.container_title == "Nature"
    request = last_request(httpx_mock)
    assert request.url.path == "/10.1038/nature12373"
    assert request.headers["accept"] == CSL_JSON


async def test_content_parses_datacite_json(client, httpx_mock):
    httpx_mock.add_response(json=DATACITE)
    record = await client.content("10.5281/zenodo.1238808", DATACITE_JSON)
    assert isinstance(record, DataciteRecord)
    assert record.doi == "10.5281/ZENODO.1238808"
    assert record.publication_year == 2018


async def test_content_parses_schemaorg_jsonld(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("cn_datacite_schemaorg.json"))
    thing = await client.content("10.5281/zenodo.1238808", SCHEMAORG_JSONLD)
    assert isinstance(thing, SchemaOrgThing)
    assert thing.type == "SoftwareSourceCode"
    assert thing.id == "https://doi.org/10.5281/zenodo.1238808"


async def test_content_returns_bibtex_and_ris_as_text(client, httpx_mock):
    bib = load_fixture("cn_crossref_bibtex.bib")
    httpx_mock.add_response(text=bib)
    text = await client.content("10.1038/nature12373", BIBTEX)
    assert isinstance(text, str)
    assert text.strip().startswith("@article")
    ris = load_fixture("cn_crossref_ris.txt")
    httpx_mock.add_response(text=ris)
    assert (await client.content("10.1038/nature12373", RIS)).startswith("TY  - JOUR")
    requests = httpx_mock.get_requests()
    assert requests[0].headers["accept"] == BIBTEX
    assert requests[1].headers["accept"] == RIS


async def test_content_follows_redirects(client, httpx_mock):
    """The client asks the framework to follow the resolver's 302."""
    httpx_mock.add_response(
        status_code=302,
        headers={"Location": "https://api.crossref.org/v1/works/x/transform"},
        text="Handle Redirect",
    )
    httpx_mock.add_response(json=CSL)
    item = await client.content("10.1038/nature12373", CSL_JSON)
    assert isinstance(item, CslItem)
    assert len(httpx_mock.get_requests()) == 2


async def test_content_rejects_empty_media_type(client, httpx_mock):
    with pytest.raises(ConfigurationError, match="non-empty"):
        await client.content("10.1038/nature12373", "  ")
    assert not httpx_mock.get_requests()


async def test_raw_returns_bytes_without_parsing(client, httpx_mock):
    body = load_fixture("redirect_crossref.html")
    httpx_mock.add_response(status_code=302, text=body)
    payload = await client.raw("10.1038/nature12373", CSL_JSON)
    assert isinstance(payload, bytes)
    assert b"Handle Redirect" in payload
    assert last_request(httpx_mock).headers["accept"] == CSL_JSON


async def test_raw_keeps_redirects_off_by_default(client, httpx_mock):
    """Without an explicit flag, the 302 itself is returned."""
    httpx_mock.add_response(
        status_code=302,
        headers={"Location": "https://api.crossref.org/v1/works/x/transform"},
        text="Handle Redirect",
    )
    payload = await client.raw("10.1038/nature12373", CSL_JSON)
    assert payload == b"Handle Redirect"
    assert len(httpx_mock.get_requests()) == 1


async def test_raw_can_follow_redirects(client, httpx_mock):
    httpx_mock.add_response(
        status_code=302,
        headers={"Location": "https://api.crossref.org/v1/works/x/transform"},
        text="Handle Redirect",
    )
    httpx_mock.add_response(json=CSL)
    payload = await client.raw("10.1038/nature12373", CSL_JSON, follow_redirects=True)
    assert b"Nanometre" in payload
    assert len(httpx_mock.get_requests()) == 2
