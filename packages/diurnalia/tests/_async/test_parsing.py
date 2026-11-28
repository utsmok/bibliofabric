"""Parsing: real payloads served through the client."""

from diurnalia import Article, Journal

from ..conftest import load_fixture

JOURNAL_PAGE = load_fixture("journal_by_issn.json")
ARTICLE_PAGE = load_fixture("article_by_doi.json")


async def test_journal_page_parses(client, httpx_mock):
    httpx_mock.add_response(json=JOURNAL_PAGE)
    page = await client.journals.search(query="issn:1932-6203")
    assert len(page.results) == 1
    record = page.results[0]
    assert isinstance(record, Journal)
    assert record.title == "PLoS ONE"
    assert page.total == 1
    assert page.page == 1
    assert page.next_cursor is None


async def test_article_page_parses(client, httpx_mock):
    httpx_mock.add_response(json=ARTICLE_PAGE)
    page = await client.articles.get("10.3389/fpubh.2020.00115")
    assert isinstance(page, Article)
    assert page.bibjson.journal is not None
    assert page.bibjson.journal.title == "Frontiers in Public Health"
