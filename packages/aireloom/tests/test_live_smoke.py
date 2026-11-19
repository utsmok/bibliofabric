"""Live smoke tests, one per resource.

Deselected by default (``-m 'not live_api'`` in ``addopts``). Run them with
``uv run pytest -m live_api``; credentials come from ``AIRELOOM_*``
environment variables or ``.env``, and anonymous access works for the
read-only calls.
"""

import pytest

from aireloom import AireloomClient, LinksFilters, ScholixFilters, relation_inverse

pytestmark = pytest.mark.live_api

DOI = "10.1038/nature12373"
ORCID = "0000-0002-1825-0097"
RP_ID = "06cdd3ff4700::3c8734759ca685b966b1d737c37daeed"


@pytest.fixture
async def live_client():
    async with AireloomClient() as aireloom:
        yield aireloom


async def test_research_products_search(live_client):
    page = await live_client.research_products.search(page_size=1)
    assert page.total and page.results
    assert page.results[0].id


async def test_research_products_get_by_id(live_client):
    page = await live_client.research_products.search(query=DOI, page_size=1)
    product = page.results[0]
    fetched = await live_client.research_products.get(product.id)
    assert fetched.id == product.id


async def test_projects_search(live_client):
    page = await live_client.projects.search(page_size=1)
    assert page.total and page.results


async def test_organizations_search(live_client):
    page = await live_client.organizations.search(page_size=1)
    assert page.total and page.results


async def test_data_sources_search(live_client):
    page = await live_client.data_sources.search(page_size=1)
    assert page.total and page.results


async def test_persons_search(live_client):
    page = await live_client.persons.search(page_size=1)
    assert page.total and page.results


async def test_links_search(live_client):
    page = await live_client.research_products.search_links(
        LinksFilters(sourcePid="10.1038/nature12373"), page_size=1
    )
    assert page.total is not None


async def test_relations_info(live_client):
    info = await live_client.research_products.get_relations_info()
    assert info and info[0].relation


async def test_scholix_links(live_client):
    page = await live_client.scholix.search_links(
        ScholixFilters(sourcePid="10.1038/nature12373"), page_size=1
    )
    assert page.results


async def test_group_by(live_client):
    counts = await live_client.research_products.group_by("type")
    assert counts.get("publication")


async def test_by_orcid(live_client):
    results = await live_client.research_products.by_orcid(ORCID, limit=5)
    assert isinstance(results, list)


async def test_find_variants(live_client):
    orgs = await live_client.organizations.find_variants(["university of twente"])
    assert orgs
    assert any(org.id.startswith("pending_org_::") for org in orgs)


async def test_get_fields(live_client):
    records = await live_client.research_products.get_fields(
        [RP_ID], ["id", "mainTitle"]
    )
    assert records and records[0].id == RP_ID


async def test_relation_vocabulary_matches_live(live_client):
    for info in await live_client.research_products.get_relations_info():
        assert relation_inverse(info.relation) == info.inverse
