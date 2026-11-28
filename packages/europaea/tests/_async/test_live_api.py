"""Live Europe PMC smoke tests against the real APIs.

Deselected by default; run with ``pytest -m live_api``. No credentials are
needed. Each test touches one route of the study documented in
``docs/europaea/upstream-quirks.md``; the suite stays small to respect
the shared host.
"""

import pytest
from bibliofabric.exceptions import NotFoundError
from europaea import (
    EuropaeaClient,
    EuropaeaSettings,
    EuropaeaSyncClient,
)

pytestmark = pytest.mark.live_api


@pytest.fixture
async def live_client():
    async with EuropaeaClient(settings=EuropaeaSettings(_env_file=None)) as client:
        yield client


async def test_search_by_doi(live_client):
    page = await live_client.search.search(
        query="DOI:10.1038/nature12373", result_type="lite", page_size=1
    )
    assert page.total == 1
    assert page.results[0].id == "23903748"
    assert page.results[0].pmcid == "PMC4221854"


async def test_search_cursor_iteration(live_client):
    records = [
        record
        async for record in live_client.search.iterate(
            query="nanodiamond AND OPEN_ACCESS:Y",
            result_type="lite",
            page_size=25,
            limit=30,
        )
    ]
    assert 0 < len(records) <= 30


async def test_article_get(live_client):
    article = await live_client.articles.get("MED:23903748")
    assert article.title and article.title.startswith("Nanometre-scale thermometry")


async def test_references_and_citations(live_client):
    references = await live_client.articles.references(
        "MED:23903748", page=1, page_size=2
    )
    assert references.total == 22
    assert references.results[0].id
    citations = await live_client.articles.citations(
        "MED:23903748", page=1, page_size=2
    )
    assert citations.total > 0


async def test_data_links_and_labs_links(live_client):
    data_links = await live_client.articles.data_links("MED:23903748")
    assert data_links.data_link_list.category[0].name == "Altmetric"
    labs_links = await live_client.articles.labs_links("MED:23903748")
    assert labs_links.hit_count is not None


async def test_full_text_xml_open_access(live_client):
    document = await live_client.articles.full_text_xml("PMC13810549")
    assert "<article" in document.xml[:400]


async def test_full_text_xml_missing_raises(live_client):
    with pytest.raises(NotFoundError):
        await live_client.articles.full_text_xml("MED/23903748")


async def test_evaluations(live_client):
    response = await live_client.articles.evaluations("MED:23903748")
    assert response.evaluation_list.evaluation == []


async def test_profile(live_client):
    response = await live_client.profiles.profile('AUTH:"Kucsko G"')
    names = {source.name for source in response.profile_list.source}
    assert "MED" in names


async def test_grants(live_client):
    response = await live_client.grants.search("malaria", page=1)
    assert int(response.hit_count) > 0
    assert response.record_list.record


async def test_annotations_by_article_ids(live_client):
    records = await live_client.annotations.by_article_ids(
        "MED:23903748", type="Chemicals"
    )
    assert records
    annotations = records[0].annotations
    assert annotations and annotations[0].type == "Chemicals"


async def test_annotations_by_entity(live_client):
    page = await live_client.annotations.by_entity("aspirin", page_size=2)
    assert page.articles
    assert page.next_cursor_mark is not None


async def test_preprints(live_client):
    page = await live_client.preprints.search(query="nanodiamond", page_size=3)
    assert page.total is not None
    assert all(record.source == "PPR" for record in page.results)


async def test_search_post_and_iteration(live_client):
    page = await live_client.search.search_post(
        query="DOI:10.1038/nature12373", result_type="lite", page_size=1
    )
    assert page.total == 1
    assert page.results[0].id == "23903748"
    records = [
        record
        async for record in live_client.search.iterate_post(
            query="nanodiamond AND OPEN_ACCESS:Y",
            result_type="lite",
            page_size=25,
            limit=30,
        )
    ]
    assert 0 < len(records) <= 30


async def test_status_updates(live_client):
    response = await live_client.articles.status_updates(
        ["PPR:PPR324115", "MED:23903748"]
    )
    metrics = response.metrics
    assert metrics is not None and metrics.articles_queried == 2
    articles = response.articles_with_status_update or []
    assert articles and articles[0].src == "PPR"
    assert articles[0].status_updates


async def test_sync_client_smoke(live_client):
    settings = live_client.settings
    with EuropaeaSyncClient(settings=settings) as client:
        page = client.search.search(
            query="DOI:10.1038/nature12373", result_type="lite", page_size=1
        )
        assert page.total == 1
