"""Record communities, record exports, top-level vocabularies, and skip handling."""

import pytest
from zenotheca import RECORD_EXPORT_FORMATS, ConfigurationError

from ..conftest import (
    COMMUNITY_SLUG,
    RECORD_ID,
    community,
    envelope,
    record,
    vocab_entry,
    vocab_envelope,
)


async def test_record_communities_route_and_parsing(client, httpx_mock):
    httpx_mock.add_response(json=envelope([community()], total=1))
    page = await client.records.communities(RECORD_ID, page_size=5)
    request = httpx_mock.get_requests()[-1]
    assert request.url.path == f"/api/records/{RECORD_ID}/communities"
    assert request.url.params["size"] == "5"
    assert page.total == 1
    assert page.results[0].slug == COMMUNITY_SLUG


async def test_export_reads_the_website_route_as_text(client, httpx_mock):
    httpx_mock.add_response(text="@misc{x,\n  title = {T}\n}")
    text = await client.records.export(f"10.5281/zenodo.{RECORD_ID}", "bibtex")
    request = httpx_mock.get_requests()[-1]
    assert str(request.url).startswith(
        f"https://zenodo.org/records/{RECORD_ID}/export/bibtex"
    )
    assert text.startswith("@misc")
    assert "bibtex" in RECORD_EXPORT_FORMATS


@pytest.mark.parametrize("fmt", ["", "  ", "a/b"])
async def test_export_rejects_bad_format_names(client, fmt):
    with pytest.raises(ConfigurationError):
        await client.records.export(RECORD_ID, fmt)


@pytest.mark.parametrize("name", ["funders", "awards", "affiliations", "subjects"])
async def test_large_vocabularies_use_their_top_level_route(client, httpx_mock, name):
    httpx_mock.add_response(json=vocab_envelope([vocab_entry("00k4n6c32")], total=1))
    page = await client.vocabularies.search(name, query="european")
    assert httpx_mock.get_requests()[-1].url.path == f"/api/{name}"
    assert page.results[0].id == "00k4n6c32"


async def test_community_records_skip_collects_invalid_records(client, httpx_mock):
    broken = record(metadata="not-an-object")
    httpx_mock.add_response(json=envelope([record(), broken], total=2))
    failures: list = []
    page = await client.communities.records(
        COMMUNITY_SLUG, on_error="skip", failures=failures
    )
    assert len(page.results) == 1
    assert [raw for raw, _ in failures] == [broken]
