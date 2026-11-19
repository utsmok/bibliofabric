"""Live API smoke tests — run with: uv run pytest tests/test_live_api.py -m live_api

These tests hit the real Crossref API and are skipped by default.
"""

import pytest

from stavrophora import StavrophoraSession
from stavrophora.endpoints import WorksFilters

pytestmark = pytest.mark.live_api

MAILTO = "s.mok@utwente.nl"


@pytest.fixture
async def session():
    async with StavrophoraSession(mailto=MAILTO) as s:
        yield s


@pytest.mark.asyncio
async def test_get_work(session):
    work = await session.works.get("10.1038/nature12373")
    assert work is not None
    assert work.doi == "10.1038/nature12373"
    assert work.primary_title


@pytest.mark.asyncio
async def test_get_journal(session):
    journal = await session.journals.get("0028-0836")
    assert journal is not None
    assert journal.primary_title == "Nature"


@pytest.mark.asyncio
async def test_get_funder(session):
    funder = await session.funders.get("10.13039/501100000923")
    assert funder is not None
    assert funder.name


@pytest.mark.asyncio
async def test_get_member(session):
    member = await session.members.get("78")
    assert member is not None
    assert member.primary_name


@pytest.mark.asyncio
async def test_get_prefix(session):
    prefix = await session.prefixes.get("10.1016")
    assert prefix is not None
    assert prefix.name


@pytest.mark.asyncio
async def test_search_works(session):
    response = await session.works.search(search="machine learning", page_size=3)
    assert response.message.total_results > 0
    assert len(response.message.items) > 0


@pytest.mark.asyncio
async def test_filter_works(session):
    filters = WorksFilters(type="journal-article", from_pub_date="2026-01-01")
    response = await session.works.search(filters=filters, page_size=3)
    assert response.message.total_results > 0


@pytest.mark.asyncio
async def test_batch_get_by_doi(session):
    found = await session.works.batch_get_by_doi(
        ["10.1038/nature12373", "10.1103/PhysRevLett.116.061102"]
    )
    assert len(found) == 2
    assert "10.1038/nature12373" in found


@pytest.mark.asyncio
async def test_scoped_journal_works(session):
    scoped = session.journals.works("0028-0836")
    response = await scoped.search(page_size=3)
    assert response.message.total_results > 0


@pytest.mark.asyncio
async def test_works_iterate(session):
    count = 0
    async for _work in session.works.iterate(page_size=3):
        count += 1
        if count >= 3:
            break
    assert count == 3
