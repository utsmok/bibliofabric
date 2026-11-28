"""Live DOAJ smoke tests against the real API.

Deselected by default; run with ``pytest -m live_api``. The API needs no
credentials. Each test fetches the same real records the fixtures in
``tests/fixtures`` were trimmed from. The default settings pace requests at
one per second, which is inside the documented limit.
"""

import pytest
from diurnalia import DiurnaliaClient, DiurnaliaSettings, NotFoundError

pytestmark = pytest.mark.live_api

PLOS_ONE_ISSN = "1932-6203"
HUNGER_DOI = "10.3389/fpubh.2020.00115"


@pytest.fixture
async def live_client():
    async with DiurnaliaClient(settings=DiurnaliaSettings(_env_file=None)) as client:
        yield client


async def test_get_journal_smoke(live_client):
    record = await live_client.journals.get(PLOS_ONE_ISSN)
    assert record.title == "PLoS ONE"
    assert record.issns == [PLOS_ONE_ISSN]
    assert record.publisher_name == "Public Library of Science (PLoS)"


async def test_get_journal_missing_issn_smoke(live_client):
    with pytest.raises(NotFoundError):
        await live_client.journals.get("1234-5678")


async def test_exists_smoke(live_client):
    assert await live_client.journals.exists(PLOS_ONE_ISSN) is True
    assert await live_client.journals.exists("1234-5678") is False


async def test_search_journals_smoke(live_client):
    page = await live_client.journals.search(query="title:plos")
    assert page.total is not None and page.total > 0
    assert len(page.results) == 10
    assert all(record.bibjson.title for record in page.results)
    assert page.meta["pageSize"] == 10


async def test_count_journals_smoke(live_client):
    assert await live_client.journals.count() == 23831


async def test_iterate_journals_smoke(live_client):
    records = [record async for record in live_client.journals.iterate(limit=20)]
    assert len(records) == 20
    assert all(record.id for record in records)


async def test_get_article_smoke(live_client):
    record = await live_client.articles.get(HUNGER_DOI)
    assert record.doi == HUNGER_DOI
    assert record.title and "Hunger" in record.title
    assert record.bibjson.author


async def test_get_by_id_smoke(live_client):
    journal = await live_client.journals.get(PLOS_ONE_ISSN)
    assert journal.id is not None
    full = await live_client.journals.get_by_id(journal.id)
    assert full.title == "PLoS ONE"
    assert full.es_type == "journal"
    assert full.admin is not None and full.admin.in_doaj is True

    article = await live_client.articles.get(HUNGER_DOI)
    assert article.id is not None
    full_article = await live_client.articles.get_by_id(article.id)
    assert full_article.doi == HUNGER_DOI
    assert full_article.es_type == "article"
    assert full_article.admin is not None and full_article.admin.in_doaj is True

    with pytest.raises(NotFoundError):
        await live_client.articles.get_by_id("0")


async def test_get_article_missing_doi_smoke(live_client):
    with pytest.raises(NotFoundError):
        await live_client.articles.get("10.9999/fpubh.2020.99999")


async def test_search_articles_smoke(live_client):
    page = await live_client.articles.search(query="title:hunger", page_size=5)
    assert page.total is not None and page.total > 0
    assert len(page.results) == 5


async def test_sort_journals_smoke(live_client):
    page = await live_client.journals.search(
        query="title:plos", page_size=5, sort="title:asc"
    )
    titles = [record.bibjson.title for record in page.results]
    assert titles == sorted(titles, key=str.casefold)
