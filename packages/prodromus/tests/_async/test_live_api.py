"""Live bioRxiv and medRxiv smoke tests against the real API.

Deselected by default; run with ``pytest -m live_api``. The API needs no
credentials.
"""

import pytest
from prodromus import NotFoundError, ProdromusClient, ProdromusSettings

pytestmark = pytest.mark.live_api


@pytest.fixture
async def live_client():
    async with ProdromusClient(settings=ProdromusSettings(_env_file=None)) as client:
        yield client


async def test_details_get_smoke(live_client):
    versions = await live_client.details.get("10.1101/339747")
    assert len(versions) >= 4
    assert versions[0].title


async def test_details_unknown_doi_smoke(live_client):
    with pytest.raises(NotFoundError):
        await live_client.details.get("10.1101/000000")


async def test_details_iterate_smoke(live_client):
    page = await live_client.details.search("medrxiv", "2026-11-01", "2026-11-01")
    assert page.total
    records = [
        record
        async for record in live_client.details.iterate(
            "medrxiv", "2026-11-01", "2026-11-01"
        )
    ]
    assert len(records) == page.total


async def test_published_and_funder_smoke(live_client):
    links = await live_client.published.get(
        "10.1101/2021.04.29.21256344", server="medrxiv"
    )
    assert links[0].published_doi == "10.1371/journal.pone.0256482"
    page = await live_client.funders.search(
        "biorxiv", "00k4n6c32", "2025-06-01", "2025-06-30"
    )
    assert page.results
    assert page.results[0].funder


async def test_statistics_smoke(live_client):
    assert await live_client.statistics.content("y")
    assert await live_client.statistics.usage("biorxiv", "y")
