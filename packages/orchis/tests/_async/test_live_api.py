"""Live ORCID smoke tests against the real public API.

Deselected by default; run with ``pytest -m live_api``. The API needs no
credentials. Each test fetches the same real record its fixture in
``tests/fixtures`` was trimmed from. The token minting test runs only when
``ORCHIS_CLIENT_ID`` and ``ORCHIS_CLIENT_SECRET`` are set (environment or
``.env``).
"""

import pytest
from orchis import NotFoundError, OrchisClient, OrchisSettings

from ..conftest import ORCID_ID, load_fixture

pytestmark = pytest.mark.live_api

CREDENTIALS = OrchisSettings()


@pytest.fixture
async def live_client():
    async with OrchisClient(
        settings=OrchisSettings(
            _env_file=None, access_token=None, client_id=None, client_secret=None
        )
    ) as client:
        yield client


@pytest.mark.skipif(
    not (CREDENTIALS.client_id and CREDENTIALS.client_secret),
    reason="set ORCHIS_CLIENT_ID and ORCHIS_CLIENT_SECRET to mint a token",
)
async def test_minted_token_reads_a_record():
    settings = CREDENTIALS.model_copy(update={"access_token": None})
    async with OrchisClient(settings=settings) as client:
        record = await client.record.get(ORCID_ID)
    assert record.orcid_identifier is not None
    assert record.orcid_identifier.path == ORCID_ID


async def test_record_smoke(live_client):
    record = await live_client.record.get(ORCID_ID)
    assert record.orcid_identifier.path == ORCID_ID
    assert record.person.name.family_name.text == "Hickey"
    assert record.activities_summary.works.put_codes()


async def test_record_exists_and_not_found_smoke(live_client):
    assert await live_client.record.exists(ORCID_ID) is True
    with pytest.raises(NotFoundError):
        await live_client.record.get("0000-0000-0000-0000")


async def test_person_sections_smoke(live_client):
    person = await live_client.person.get(ORCID_ID)
    assert person.name.given_names.text == "Thomas B."
    assert len(person.researcher_urls.researcher_url) >= 1
    assert await live_client.person.biography(ORCID_ID) is None
    assert await live_client.person.emails(ORCID_ID) is None
    assert await live_client.person.external_identifiers(ORCID_ID) is not None


async def test_activities_sections_smoke(live_client):
    summary = await live_client.activities.get(ORCID_ID)
    assert summary.educations.put_codes()[:1] == [85904]
    works = await live_client.activities.works(ORCID_ID)
    assert works is not None and works.put_codes()
    distinctions = await live_client.activities.distinctions(ORCID_ID)
    # The API answers 404 or an empty group for unused sections, varying run
    # to run (observed both on 2026-11-27).
    assert distinctions is None or distinctions.affiliation_group == []


async def test_single_items_smoke(live_client):
    work = await live_client.activities.work(ORCID_ID, 145464015)
    assert work.title.title.text == "Parsing and Matching Dates in VIAF"
    education = await live_client.activities.education(ORCID_ID, 85904)
    assert education["put-code"] == 85904
    funding = await live_client.activities.funding(ORCID_ID, 63665)
    assert funding.organization.name == "NSF Office of the Director"


async def test_work_representation_smoke(live_client):
    body = await live_client.activities.representation(ORCID_ID, "work/145464015")
    assert "<work:" in body or "<work" in body


async def test_expanded_search_smoke(live_client):
    page = await live_client.expanded_search.search(
        query="family-name:Kucsko", page_size=2
    )
    assert page.total is not None and page.total >= 1
    assert page.results[0].family_names == "Kucsko"


async def test_solr_search_smoke(live_client):
    page = await live_client.search.search(query="family-name:Kucsko", page_size=2)
    assert page.total >= 1
    assert page.results[0].orcid_identifier.host == "orcid.org"


async def test_paging_smoke(live_client):
    page = await live_client.expanded_search.search(
        query="family-name:Kucsko", page_size=2, page=1
    )
    load = load_fixture("expanded_search_page.json")
    assert page.results == []
    assert page.total == load["num-found"]
