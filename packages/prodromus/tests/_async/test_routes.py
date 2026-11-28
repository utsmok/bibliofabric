"""Request paths, cursor paging, status handling, and parsing per route."""

import pytest
from prodromus import ConfigurationError, NotFoundError

from ..conftest import envelope, load_fixture

BASE = "https://api.biorxiv.org"


def last_url(httpx_mock) -> str:
    return str(httpx_mock.get_requests()[-1].url)


async def test_details_get_returns_every_version(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("details_doi.json"))
    versions = await client.details.get("https://doi.org/10.1101/339747")
    assert last_url(httpx_mock) == f"{BASE}/details/biorxiv/10.1101/339747/na/json"
    assert [version.version_number for version in versions] == [1, 2, 3, 4]
    assert versions[0].published_doi is None
    assert versions[0].author_list[0] == "Kvich, L. A."


async def test_details_get_unknown_doi_raises(client, httpx_mock):
    httpx_mock.add_response(
        json={"messages": [{"status": "no posts found"}], "collection": []}
    )
    with pytest.raises(NotFoundError):
        await client.details.get("10.1101/000000", server="medrxiv")


async def test_details_search_builds_range_cursor_and_category(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("details_interval.json"))
    page = await client.details.search(
        "medRxiv",
        "2026-11-01",
        "2026-11-01",
        cursor=0,
        category="Cardiovascular Medicine",
    )
    assert last_url(httpx_mock) == (
        f"{BASE}/details/medrxiv/2026-11-01/2026-11-01/0"
        "?category=cardiovascular_medicine"
    )
    assert page.total == 43
    assert page.next_cursor == "30"
    assert page.results[0].server == "medRxiv"


async def test_details_iterate_follows_the_cursor(client, httpx_mock):
    record = load_fixture("details_doi.json")["collection"][0]
    for cursor, count in ((0, 30), (30, 30), (60, 1)):
        httpx_mock.add_response(
            url=f"{BASE}/details/biorxiv/2026-11-01/2026-11-02/{cursor}",
            json=envelope([record] * count, cursor=cursor, count=count, total=61),
        )
    records = [
        preprint
        async for preprint in client.details.iterate(
            "biorxiv", "2026-11-01", "2026-11-02"
        )
    ]
    assert len(records) == 61


async def test_recent_uses_the_cursorless_forms(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("details_interval.json"))
    await client.details.recent("biorxiv", days=2)
    assert last_url(httpx_mock) == f"{BASE}/details/biorxiv/2d"
    httpx_mock.add_response(json=load_fixture("details_interval.json"))
    await client.details.recent("biorxiv", posts=45)
    assert last_url(httpx_mock) == f"{BASE}/details/biorxiv/45"
    with pytest.raises(ConfigurationError):
        await client.details.recent("biorxiv", posts=5, days=5)


async def test_error_status_with_http_200_raises(client, httpx_mock):
    httpx_mock.add_response(
        json={
            "messages": [{"status": "Both dates must be in yyyy-mm-dd format"}],
            "collection": [],
        }
    )
    with pytest.raises(ConfigurationError, match="yyyy-mm-dd"):
        await client.details.search("biorxiv", "2026-11-01", "2026-11-02")


@pytest.mark.parametrize(
    ("args", "kwargs"),
    [
        (("arxiv", "2026-11-01", "2026-11-02"), {}),
        (("biorxiv", "2026/11/01", "2026-11-02"), {}),
        (("biorxiv", "2026-11-03", "2026-11-02"), {}),
        (("biorxiv", "2026-11-01", "2026-11-02"), {"cursor": -1}),
    ],
)
async def test_guards_reject_bad_arguments(client, args, kwargs):
    with pytest.raises(ConfigurationError):
        await client.details.search(*args, **kwargs)


async def test_published_routes(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("pubs_doi.json"))
    links = await client.published.get("10.1371/journal.pone.0256482", server="medrxiv")
    assert last_url(httpx_mock) == (
        f"{BASE}/pubs/medrxiv/10.1371/journal.pone.0256482/na/json"
    )
    assert links[0].preprint == "10.1101/2021.04.29.21256344"
    assert links[0].published_journal == "PLOS ONE"
    httpx_mock.add_response(json=load_fixture("pub.json"))
    page = await client.published.biorxiv("2026-11-01", "2026-11-02")
    assert last_url(httpx_mock) == f"{BASE}/pub/2026-11-01/2026-11-02/0"
    assert page.results[0].preprint == "10.64898/2026.03.19.712977"
    assert page.next_cursor is None
    httpx_mock.add_response(
        json={"messages": [{"status": "no articles found"}], "collection": []}
    )
    page = await client.published.by_publisher("10.15252", "2026-11-01", "2026-11-30")
    assert last_url(httpx_mock) == f"{BASE}/publisher/10.15252/2026-11-01/2026-11-30/0"
    assert page.results == []
    with pytest.raises(ConfigurationError):
        await client.published.by_publisher("10.15252/embj", "2026-11-01", "2026-11-30")


async def test_funder_route_takes_a_ror_id(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("funder.json"))
    page = await client.funders.search(
        "biorxiv", "https://ror.org/00k4n6c32", "2025-06-01", "2025-06-30"
    )
    assert last_url(httpx_mock) == (
        f"{BASE}/funder/biorxiv/2025-06-01/2025-06-30/00k4n6c32/0"
    )
    funder = page.results[0].funder[0]
    assert funder.name == "European Commission"
    assert funder.id_type == "ROR"


async def test_statistics_routes(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("sum.json"))
    content = await client.statistics.content("y")
    assert last_url(httpx_mock) == f"{BASE}/sum/y"
    assert content[0].year == 2013
    assert content[0].new_papers == 109
    httpx_mock.add_response(json=load_fixture("usage.json"))
    usage = await client.statistics.usage("medrxiv", "y")
    assert last_url(httpx_mock) == f"{BASE}/usage/y/medrxiv"
    assert usage[0].abstract_views == 3277367
    with pytest.raises(ConfigurationError):
        await client.statistics.content("d")
