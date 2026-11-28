"""Parsing: real payloads through the resource clients, flattening, meta."""

from dataphora import DataphoraClient

from ..conftest import doi_resource, envelope, load_fixture

DOI = load_fixture("doi.json")
PAGE = load_fixture("dois_list.json")
QUERY_PAGE = load_fixture("dois_query.json")
CLIENT = load_fixture("client.json")
PROVIDER = load_fixture("provider.json")
REPOSITORY = load_fixture("repository.json")
PREFIX = load_fixture("prefix.json")
ACTIVITY = load_fixture("doi_activities.json")


async def test_doi_record_from_real_payload(client, httpx_mock):
    httpx_mock.add_response(json=DOI)
    doi = await client.dois.get("10.5438/0012")
    assert doi.id == "10.5438/0012"
    assert doi.title.startswith("DataCite Metadata Schema Documentation")
    assert doi.resource_type == "Text"
    assert doi.publicationYear == 2016
    assert doi.publisher == "DataCite e.V."
    assert doi.state == "findable"
    assert doi.client_id == "datacite.datacite"
    assert doi.provider_id == "datacite"
    assert doi.creators[0].name == "DataCite Metadata Working Group"


async def test_doi_relationships_survive_parsing(client, httpx_mock):
    httpx_mock.add_response(json=DOI)
    doi = await client.dois.get("10.5438/0012")
    assert doi.relationships is not None
    assert set(doi.relationships) >= {"client", "provider", "media", "references"}
    assert doi.links is None


async def test_search_page_parses_and_flattens(client, httpx_mock):
    httpx_mock.add_response(json=PAGE)
    page = await client.dois.search()
    assert page.total == PAGE["meta"]["total"]
    assert page.page == 1
    assert page.next_cursor is None
    first = page.results[0]
    assert first.doi == PAGE["data"][0]["attributes"]["doi"]
    assert first.state == "findable"
    assert first.resource_type == "Preprint"


async def test_search_page_meta_keeps_the_envelope_links(client, httpx_mock):
    httpx_mock.add_response(json=QUERY_PAGE)
    page = await client.dois.search(query="climate change")
    assert page.total == QUERY_PAGE["meta"]["total"]
    links = page.meta["links"]
    assert "page%5Bnumber%5D=2" in links["next"]
    requests = httpx_mock.get_requests()
    assert dict(requests[-1].url.params)["query"] == "climate change"


async def test_client_record_from_real_payload(client, httpx_mock):
    httpx_mock.add_response(json=envelope(CLIENT["data"]))
    record = await client.clients.first()
    assert record is not None
    assert record.id == CLIENT["data"][0]["id"]
    assert record.symbol == CLIENT["data"][0]["attributes"]["symbol"]
    assert record.clientType == "periodical"


async def test_provider_record_from_real_payload(client, httpx_mock):
    httpx_mock.add_response(json=envelope(PROVIDER["data"]))
    record = await client.providers.first()
    assert record is not None
    assert record.memberType == "direct_member"
    assert record.region == "EMEA"


async def test_repository_record_from_real_payload(client, httpx_mock):
    httpx_mock.add_response(json=envelope(REPOSITORY["data"]))
    record = await client.repositories.first()
    assert record is not None
    assert record.id == REPOSITORY["data"][0]["id"]
    assert record.clientType == REPOSITORY["data"][0]["attributes"]["clientType"]


async def test_prefix_record_from_real_payload(client, httpx_mock):
    httpx_mock.add_response(json=envelope(PREFIX["data"]))
    record = await client.prefixes.first()
    assert record is not None
    assert record.prefix == record.id == "10.10273"
    assert record.createdAt is not None


async def test_activities_from_real_payload(client, httpx_mock):
    httpx_mock.add_response(json=ACTIVITY)
    activities = await client.dois.activities("10.5438/0012")
    assert len(activities) == 1
    activity = activities[0]
    assert activity.action == "update"
    assert activity.version == 81
    assert activity.changes is not None
    assert "titles" in activity.changes
    assert any(key.startswith("prov:") for key in (activity.model_extra or {}))


async def test_global_activities_from_real_payload(client, httpx_mock):
    httpx_mock.add_response(json=ACTIVITY)
    activities = await client.activities.search(page_size=1)
    assert activities.results
    assert activities.results[0].action == "update"


async def test_event_from_real_payload(client, httpx_mock):
    payload = load_fixture("event.json")
    httpx_mock.add_response(json=payload)
    page = await client.events.search({"doi": "10.5438/0012"})
    event = page.results[0]
    assert event.id == payload["data"][0]["id"]
    assert event.relation_type_id == "total-resolutions-machine"
    assert event.source_id == "datacite-resolution"
    assert event.occurred_at == "2019-06-01T00:00:00.000Z"
    assert event.subj_id is not None
    assert event.obj_id == "https://doi.org/10.5438/0012"


async def test_totals_from_real_payload(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("clients_totals.json"))
    totals = await client.clients.totals()
    assert totals
    assert totals[0].id == "rpht.nifs"
    assert totals[0].count == 46241024
    assert totals[0].temporal is not None
    assert "this_year" in totals[0].temporal


async def test_prefix_assignments_from_real_payload(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("client_prefixes.json"))
    httpx_mock.add_response(json=load_fixture("provider_prefixes.json"))
    client_prefixes = await client.client_prefixes.search()
    provider_prefixes = await client.provider_prefixes.search()
    assignment = client_prefixes.results[0]
    assert assignment.createdAt is not None
    assert assignment.relationships is not None
    assert "prefix" in assignment.relationships
    assert "client" in assignment.relationships
    provider_assignment = provider_prefixes.results[0]
    assert provider_assignment.relationships is not None
    assert "provider" in provider_assignment.relationships
    assert "prefix" in provider_assignment.relationships


async def test_unknown_attributes_are_kept_as_extras(client, httpx_mock):
    httpx_mock.add_response(
        json=envelope([doi_resource("10.5438/9", brandNewField=42)])
    )
    page = await client.dois.search()
    assert page.results[0].model_extra == {"brandNewField": 42}


def test_client_exposes_all_resources(settings):
    client = DataphoraClient(settings=settings)
    assert client.dois is client.dois
    assert client.activities is client.activities
    assert client.clients is client.clients
    assert client.client_prefixes is client.client_prefixes
    assert client.providers is client.providers
    assert client.provider_prefixes is client.provider_prefixes
    assert client.repositories is client.repositories
    assert client.prefixes is client.prefixes
    assert client.events is client.events
