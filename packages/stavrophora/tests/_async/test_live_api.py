"""Live smoke tests against api.crossref.org, one per resource.

Deselected by default (``-m 'not live_api'``). Run with a polite-pool email:

    STAVROPHORA_MAILTO=you@example.org uv run pytest -m live_api
"""

import os

import pytest
from stavrophora import StavrophoraClient, WorksFilters

MAILTO = os.environ.get("STAVROPHORA_MAILTO", "")

pytestmark = [
    pytest.mark.live_api,
    pytest.mark.skipif(not MAILTO, reason="set STAVROPHORA_MAILTO to run live checks"),
]


@pytest.fixture
async def live_client():
    async with StavrophoraClient(mailto=MAILTO) as client:
        yield client


async def test_works_get(live_client):
    work = await live_client.works.get("https://doi.org/10.1038/Nature12373")
    assert work.doi == "10.1038/nature12373"
    assert work.title


async def test_works_search(live_client):
    page = await live_client.works.search(
        WorksFilters(type="journal-article", from_pub_date="2024-01-01"),
        query="proteomics",
        sort="is-referenced-by-count:desc",
        select=["DOI", "title", "is-referenced-by-count"],
        page_size=5,
    )
    assert page.total > 0
    assert len(page.results) == 5
    assert page.results[0].title


async def test_works_count(live_client):
    assert await live_client.works.count(query="crispr") > 0


async def test_works_iterate(live_client):
    seen = []
    async for work in live_client.works.iterate(query="crispr", limit=5):
        seen.append(work)
        if len(seen) >= 5:
            break
    assert len(seen) == 5


async def test_works_facets(live_client):
    facets = await live_client.works.facets(query="crispr", facets=("type-name",))
    assert facets["type-name"]


async def test_works_sample(live_client):
    page = await live_client.works.sample(3)
    assert len(page.results) == 3


async def test_works_agency(live_client):
    agency = await live_client.works.agency("10.1038/nature12373")
    assert agency.agency is not None


async def test_works_batch_get_by_doi(live_client):
    works = await live_client.works.batch_get_by_doi(
        ["10.1038/nature12373", "10.1093/hesc/9780198807506.003.0005"]
    )
    assert set(works) == {"10.1038/nature12373", "10.1093/hesc/9780198807506.003.0005"}


async def test_works_exists(live_client):
    assert await live_client.works.exists("10.1038/nature12373") is True
    assert await live_client.works.exists("10.9999/stavrophora-smoke") is False


async def test_works_latest_version(live_client):
    latest = await live_client.works.latest_version("10.12688/f1000research.141553.2")
    assert latest.doi != "10.12688/f1000research.141553.2"


async def test_journals(live_client):
    journal = await live_client.journals.get("20493630")
    assert journal.primary_title
    page = await live_client.journals.search(query="neurology", page_size=2)
    assert page.results


async def test_journals_dois_by_year(live_client):
    counts = await live_client.journals.dois_by_year("20493630")
    assert sum(counts.values()) > 0


async def test_funders(live_client):
    funder = await live_client.funders.get("10.13039/100000001")
    assert funder.name == "National Science Foundation"
    page = await live_client.funders.search(query="boeing", page_size=2)
    assert page.results


async def test_funders_descendants(live_client):
    descendants = await live_client.funders.descendants("10.13039/100000002")
    assert descendants
    page = await live_client.funders.works(
        "10.13039/100000002", include_descendants=True
    ).search(page_size=2)
    assert len(page.results) == 2


async def test_members(live_client):
    member = await live_client.members.get(297)
    assert member.id == 297
    page = await live_client.members.works(297).search(page_size=2)
    assert page.results


async def test_types(live_client):
    type_ = await live_client.types.get("journal-article")
    assert type_.label
    page = await live_client.types.search()
    assert page.results


async def test_prefixes(live_client):
    prefix = await live_client.prefixes.get("10.1038")
    assert prefix.prefix == "10.1038"


async def test_licenses(live_client):
    page = await live_client.licenses.search(page_size=2)
    assert page.results
