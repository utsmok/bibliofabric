"""Fixture-driven parsing through the client against real payloads."""

from quiddita import Entity, RestItem, SparqlResult

from ..conftest import load_fixture


async def test_full_entity_fixture_through_client(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("entity_q42.json"))
    result = await client.entities.get("Q42")
    assert isinstance(result, Entity)
    assert result.claims["P570"][0].mainsnak.datavalue.value["precision"] == 11
    assert result.sitelinks["nlwiki"].site == "nlwiki"


async def test_rest_item_fixture_through_client(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("rest_item_q42.json"))
    item = await client.items.get("Q42")
    assert isinstance(item, RestItem)
    statement = item.statements["P569"][0]
    assert statement.references[0].parts[0].property.id == "P248"


async def test_rest_search_fixture_through_client(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("rest_search_items.json"))
    results = await client.search.search_items("Douglas Adams")
    assert results[0].display_label.value == "Douglas Adams"


async def test_sparql_fixture_through_client(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("sparql_result.json"))
    result = await client.sparql.query("SELECT ?item ?l WHERE { ?item wdt:P31 wd:Q5 }")
    assert isinstance(result, SparqlResult)
    assert "l" in result.head.vars
