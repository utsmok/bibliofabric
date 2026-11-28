"""Live ISSN Portal smoke tests against the real site.

Paced by the client settings (1 request per second by default). The live
run costs about 12 requests.
"""

import pytest
from bibliofabric.exceptions import ConfigurationError, NotFoundError
from seriatim import (
    IssnLRecord,
    LtwaEntry,
    SearchHit,
    SeriatimClient,
    SeriatimRecord,
    SeriatimSettings,
)

pytestmark = pytest.mark.live_api

NATURE = "0028-0836"


@pytest.fixture
async def live_client():
    async with SeriatimClient(settings=SeriatimSettings(_env_file=None)) as client:
        yield client


async def test_get_record_smoke(live_client):
    record = await live_client.records.get(NATURE)
    assert isinstance(record, SeriatimRecord)
    assert record.issn == NATURE
    assert record.format == "medium:Print"
    assert record.main_entity_of.status == "recordStatus:Register"
    assert record.raw["@context"]["@base"].endswith(f"ISSN/{NATURE}")


async def test_get_record_check_digit_x_smoke(live_client):
    record = await live_client.records.get("2434-561X")
    assert record.issn == "2434-561X"
    assert record.format == "medium:Online"


async def test_get_cancelled_record_smoke(live_client):
    record = await live_client.records.get("0302-2889")
    assert record.issn == "0302-2889"
    assert record.main_entity_of.status == "recordStatus:Cancelled"


async def test_get_not_found_smoke(live_client):
    with pytest.raises(NotFoundError):
        await live_client.records.get("9999-9994")


async def test_invalid_issn_raises_before_request(live_client):
    with pytest.raises(ConfigurationError, match="valid ISSN"):
        await live_client.records.get("9999-9999")


async def test_get_issn_l_smoke(live_client):
    cluster = await live_client.issn_l.get(NATURE)
    assert isinstance(cluster, IssnLRecord)
    assert cluster.issn_l == NATURE
    assert {part.format for part in cluster.has_part} >= {"medium:Print"}


async def test_exists_smoke(live_client):
    assert await live_client.records.exists(NATURE) is True
    assert await live_client.records.exists("9999-9994") is False


async def test_search_page_smoke(live_client):
    page = await live_client.search.page(NATURE)
    assert page.total is not None and page.total > 0
    assert page.hits
    hit = page.hits[0]
    assert isinstance(hit, SearchHit)
    assert hit.issn == NATURE
    assert hit.title
    assert hit.medium in {"ta", "cr"}


async def test_search_iterate_limit_smoke(live_client):
    hits = [hit async for hit in live_client.search.iterate("nature", limit=3)]
    assert len(hits) == 3
    assert all(isinstance(hit, SearchHit) for hit in hits)


async def test_ltwa_page_smoke(live_client):
    page = await live_client.ltwa.page(page_size=20)
    assert page.entries
    entry = page.entries[0]
    assert isinstance(entry, LtwaEntry)
    assert entry.word
    assert entry.language


async def test_ltwa_iterate_limit_smoke(live_client):
    entries = [entry async for entry in live_client.ltwa.iterate(limit=5)]
    assert len(entries) == 5
    assert {entry.word for entry in entries}
