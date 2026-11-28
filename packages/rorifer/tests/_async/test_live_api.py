"""Live ROR smoke tests against the real API.

Deselected by default; run with ``uv run pytest -m live_api``. The API needs
no credentials. Each test fetches the same real record its fixture in
``tests/fixtures`` was trimmed from.
"""

import pytest
from rorifer import (
    ConfigurationError,
    NotFoundError,
    OrganizationFilters,
    RoriferClient,
    RoriferSettings,
    index_external_ids,
    iter_dump_records,
)

from ..conftest import load_fixture

pytestmark = pytest.mark.live_api

UNIVERSITY_OF_TWENTE = "https://ror.org/006hf6230"
NSF = "https://ror.org/021nxhr62"


@pytest.fixture
async def live_client():
    async with RoriferClient(settings=RoriferSettings(_env_file=None)) as client:
        yield client


async def test_get_smoke(live_client):
    record = await live_client.organizations.get("https://ror.org/006hf6230")
    assert record.id == UNIVERSITY_OF_TWENTE
    assert record.display_name == "University of Twente"
    assert record.locations[0].geonames_details.country_code == "NL"


async def test_get_inactive_record_smoke(live_client):
    record = await live_client.organizations.get("001z21q04")
    assert record.status == "inactive"


async def test_get_not_found_smoke(live_client):
    with pytest.raises(NotFoundError):
        await live_client.organizations.get("00yjdzt39")


async def test_exists_smoke(live_client):
    assert await live_client.organizations.exists("006hf6230") is True
    assert await live_client.organizations.exists("00yjdzt39") is False


async def test_search_smoke(live_client):
    page = await live_client.organizations.search(query="university of twente")
    assert page.total is not None and page.total > 0
    assert page.results[0].id == UNIVERSITY_OF_TWENTE
    assert page.meta["statuses"][0]["id"] == "active"
    assert len(page.results) == 20


async def test_search_filters_advanced_and_all_status_smoke(live_client):
    page = await live_client.organizations.search(
        OrganizationFilters(
            types=["education", "nonprofit"], country_country_code="NL"
        ),
        advanced="established:[1900 TO 2000]",
        all_status=True,
    )
    assert page.results
    for record in page.results:
        assert "NL" in {
            location.geonames_details.country_code
            for location in record.locations
            if location.geonames_details is not None
        }


async def test_search_rejects_query_with_advanced_smoke(live_client):
    with pytest.raises(ConfigurationError, match="cannot be combined"):
        await live_client.organizations.search(
            query="university", advanced="established:[1900 TO 2000]"
        )


async def test_rejected_filter_smoke(live_client):
    with pytest.raises(ConfigurationError, match="illegal"):
        await live_client.organizations.search({"country": "nl"})


async def test_count_smoke(live_client):
    assert await live_client.organizations.count(query="university of twente") > 0


async def test_iterate_three_pages_smoke(live_client):
    records = [
        record
        async for record in live_client.organizations.iterate(
            query="university of twente", limit=60
        )
    ]
    assert len(records) == 60
    assert all(
        record.id and record.id.startswith("https://ror.org/") for record in records
    )


async def test_match_affiliation_smoke(live_client):
    matches = await live_client.organizations.match_affiliation(
        "University of Twente, Enschede, Netherlands"
    )
    chosen = [match for match in matches if match.chosen]
    assert len(chosen) == 1
    assert chosen[0].organization is not None
    assert chosen[0].organization.id == UNIVERSITY_OF_TWENTE


async def test_find_by_external_id_smoke(live_client):
    isni = load_fixture("organization.json")["external_ids"][2]["all"][0]
    found = await live_client.organizations.find_by_external_id(isni, id_type="isni")
    assert [record.id for record in found] == [UNIVERSITY_OF_TWENTE]
    nsf = await live_client.organizations.find_by_funder_doi("10.13039/100000001")
    assert [record.id for record in nsf] == [NSF]


async def test_heartbeat_smoke(live_client):
    assert await live_client.heartbeat() is True


async def test_dumps_list_smoke(live_client):
    """Every release is one Zenodo record; a search without ``all_versions`` answers three."""
    dumps = await live_client.dumps.list(limit=3)
    assert len(dumps) == 3
    assert len({dump.record_id for dump in dumps}) == 3
    assert all(dump.version for dump in dumps)
    assert dumps[0].zip_url
    latest = await live_client.dumps.latest()
    assert latest.publication_date is not None
    assert latest.publication_date >= dumps[0].publication_date


async def test_dump_download_and_read_smoke(live_client, tmp_path):
    latest = await live_client.dumps.latest()
    path = await live_client.dumps.download(latest, tmp_path / "ror-data.zip")
    assert path.stat().st_size > 1_000_000
    records = list(iter_dump_records(path))
    assert len(records) > 100_000
    fundref = index_external_ids(records, "fundref")
    assert "100000001" in fundref
