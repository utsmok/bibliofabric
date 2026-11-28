"""Live DataCite smoke tests against the real API.

Public reads need no credentials. Tests stay lean so the anonymous budget of
500 requests per 5 minutes is never at risk.
"""

import pytest
from bibliofabric import NotFoundError
from dataphora import (
    DataphoraClient,
    DataphoraSettings,
    PrefixFilters,
    ProviderFilters,
)

pytestmark = pytest.mark.live_api

SCHEMA_DOI = "10.5438/0012"
DATACITE_CLIENT = "datacite.datacite"


@pytest.fixture
async def live_client():
    async with DataphoraClient(settings=DataphoraSettings(_env_file=None)) as client:
        yield client


async def test_get_doi_smoke(live_client):
    doi = await live_client.dois.get(SCHEMA_DOI)
    assert doi.doi == SCHEMA_DOI
    assert doi.state == "findable"
    assert doi.title


async def test_get_doi_not_found_smoke(live_client):
    with pytest.raises(NotFoundError):
        await live_client.dois.get("10.5438/nosuchdoi9999")


async def test_graphql_query_smoke(live_client):
    data = await live_client.graphql.query(
        "query($id: ID!) { work(id: $id) { doi publicationYear types "
        "{ resourceTypeGeneral } } }",
        {"id": f"https://doi.org/{SCHEMA_DOI}"},
    )
    assert data["work"]["doi"] == SCHEMA_DOI
    assert data["work"]["types"]["resourceTypeGeneral"] == "Text"


async def test_exists_smoke(live_client):
    assert await live_client.dois.exists(SCHEMA_DOI) is True
    assert await live_client.dois.exists("10.5438/nosuchdoi9999") is False


async def test_search_and_filters_smoke(live_client):
    page = await live_client.dois.search(
        {"client-id": DATACITE_CLIENT, "resource-type-id": "text"},
        query="metadata schema",
        select=["doi", "titles"],
    )
    assert page.results
    record = page.results[0]
    assert record.doi
    assert record.titles


async def test_count_smoke(live_client):
    total = await live_client.dois.count({"prefix": "10.5438"})
    assert total > 0


async def test_iterate_limit_smoke(live_client):
    records = [
        record
        async for record in live_client.dois.iterate({"prefix": "10.5438"}, limit=3)
    ]
    assert len(records) == 3
    assert all(record.created for record in records)


async def test_activities_smoke(live_client):
    activities = await live_client.dois.activities(SCHEMA_DOI)
    assert activities
    assert activities[0].action


async def test_clients_smoke(live_client):
    record = await live_client.clients.get(DATACITE_CLIENT)
    assert record.id == DATACITE_CLIENT
    assert record.symbol == "DATACITE.DATACITE"
    page = await live_client.clients.search(query="zenodo", page_size=5)
    assert page.results


async def test_client_dois_smoke(live_client):
    page = await live_client.clients.dois(DATACITE_CLIENT, page_size=1)
    assert page.results
    assert page.results[0].client_id == DATACITE_CLIENT


async def test_providers_smoke(live_client):
    record = await live_client.providers.get("datacite")
    assert record.id == "datacite"
    page = await live_client.providers.search(page_size=5)
    assert page.total and page.total > 1000


async def test_repositories_smoke(live_client):
    record = await live_client.repositories.get(DATACITE_CLIENT)
    assert record.id == DATACITE_CLIENT
    page = await live_client.repositories.search(query="zenodo", page_size=5)
    assert page.results


async def test_prefixes_smoke(live_client):
    record = await live_client.prefixes.get("10.5438")
    assert record.prefix == "10.5438"
    page = await live_client.prefixes.search(page_size=5)
    assert page.results


async def test_prefix_dois_smoke(live_client):
    page = await live_client.prefixes.dois("10.5438", page_size=1)
    assert page.results


async def test_client_prefixes_smoke(live_client):
    page = await live_client.client_prefixes.search(page_size=1)
    assert page.results


async def test_provider_prefixes_smoke(live_client):
    page = await live_client.provider_prefixes.search(page_size=1)
    assert page.results


async def test_events_smoke(live_client):
    page = await live_client.events.search({"doi": SCHEMA_DOI}, page_size=2)
    assert page.results
    assert page.results[0].relation_type_id


async def test_heartbeat_smoke(live_client):
    assert await live_client.heartbeat() is True


async def test_global_activities_smoke(live_client):
    """``query`` finds the activities of one DOI; the ``id`` filters answer
    nothing without a login."""
    listed = await live_client.activities.search(query=f'"{SCHEMA_DOI}"', page_size=5)
    scoped = await live_client.dois.activities(SCHEMA_DOI)
    assert scoped
    assert {activity.id for activity in listed.results} == {
        activity.id for activity in scoped
    }
    assert scoped[0].prov_was_derived_from == f"https://doi.org/{SCHEMA_DOI}"


async def test_account_activities_smoke(live_client):
    client_page = await live_client.clients.activities(DATACITE_CLIENT, page_size=5)
    assert client_page.results
    assert client_page.next_cursor is None
    assert client_page.results[0].prov_was_derived_from is not None
    assert client_page.results[0].prov_was_derived_from.endswith(DATACITE_CLIENT)
    provider_page = await live_client.providers.activities("datacite", page_size=5)
    assert provider_page.results
    assert provider_page.next_cursor is None


async def test_totals_smoke(live_client):
    prefixes = await live_client.prefixes.totals("cern.zenodo")
    assert [entry.id for entry in prefixes] == ["10.5281"]
    assert await live_client.prefixes.totals("nosuch.client9999") == []
    clients = await live_client.clients.totals(provider_id="cern")
    assert clients
    assert all(entry.id.startswith("cern.") for entry in clients)
    providers = await live_client.providers.totals()
    assert "datacite" in {entry.id for entry in providers}


async def test_filter_models_smoke(live_client):
    page = await live_client.providers.search(
        ProviderFilters(region="apac"), page_size=5
    )
    assert page.results
    assert {record.region for record in page.results} == {"APAC"}
    unassigned = await live_client.prefixes.count(PrefixFilters(state="unassigned"))
    without_repository = await live_client.prefixes.count(
        PrefixFilters(state="without-repository")
    )
    assert unassigned > 0
    assert without_repository > 0
    assert unassigned != without_repository


async def test_repositories_serve_periodicals_too_smoke(live_client):
    """``/repositories`` is an alias of ``/clients``, not a filtered view."""
    periodical = await live_client.repositories.get("rhtq.rjxpkl")
    assert periodical.clientType == "periodical"
