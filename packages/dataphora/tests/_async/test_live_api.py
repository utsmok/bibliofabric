"""Live DataCite smoke tests against the real API.

Public reads need no credentials. Tests stay lean so the anonymous budget of
500 requests per 5 minutes is never at risk.
"""

import pytest
from bibliofabric import NotFoundError
from dataphora import DataphoraClient, DataphoraSettings

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
