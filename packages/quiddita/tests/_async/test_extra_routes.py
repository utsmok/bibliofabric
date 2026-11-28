"""Request shapes and typed results of the extra read routes.

EntityData, REST suggest, lexeme REST, and the Action utility modules.
"""

import pytest
from bibliofabric.exceptions import ConfigurationError

from ..conftest import load_fixture
from .test_request_shape import last_params, last_request


async def test_entity_data_json_parses_entity(client, httpx_mock):
    httpx_mock.add_response(
        json=load_fixture("entity_data_q42.json"),
        headers={"content-type": "application/json; charset=UTF-8"},
    )
    result = await client.entity_data.get("Q42")
    assert result.format == "json"
    assert result.content_type == "application/json"
    assert result.entity is not None
    assert result.entity.id == "Q42"
    assert result.document is None
    assert last_request(httpx_mock).url.path == "/wiki/Special:EntityData/Q42.json"


async def test_entity_data_ttl_returns_document(client, httpx_mock):
    httpx_mock.add_response(
        text="@prefix wikibase: <http://wikiba.se/ontology#> .",
        headers={"content-type": "text/turtle; charset=UTF-8"},
    )
    result = await client.entity_data.get("Q42", format="ttl")
    assert result.entity is None
    assert result.document is not None
    assert result.document.format == "ttl"
    assert result.document.content_type == "text/turtle"
    assert result.document.text.startswith("@prefix")


async def test_entity_data_revision_and_format(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("entity_data_q42.json"))
    await client.entity_data.get("P31", format="rdf", revision=2575435918)
    request = last_request(httpx_mock)
    assert request.url.path == "/wiki/Special:EntityData/P31.rdf"
    assert request.url.params["revision"] == "2575435918"


async def test_entity_data_bad_format_rejected_locally(client, httpx_mock):
    with pytest.raises(ConfigurationError, match="format must be one of"):
        await client.entity_data.get("Q42", format="nquads")
    assert not httpx_mock.get_requests()


async def test_entity_data_negotiate_follows_entity_route(client, httpx_mock):
    httpx_mock.add_response(
        text="@prefix wikibase: <http://wikiba.se/ontology#> .",
        headers={"content-type": "text/turtle; charset=UTF-8"},
    )
    document = await client.entity_data.negotiate("Q42", accept="text/turtle")
    assert document.content_type == "text/turtle"
    request = last_request(httpx_mock)
    assert request.url.path == "/entity/Q42"
    assert request.headers["accept"] == "text/turtle"


async def test_suggest_items_request_and_result(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("suggest_items.json"))
    results = await client.search.suggest_items("einstein", language="en", limit=3)
    assert "Q937" in [hit.id for hit in results]
    hit = next(hit for hit in results if hit.id == "Q937")
    assert hit.display_label.value == "Albert Einstein"
    request = last_request(httpx_mock)
    assert request.url.path == "/w/rest.php/wikibase/v1/suggest/items"
    params = dict(request.url.params)
    assert params["q"] == "einstein"
    assert params["language"] == "en"
    assert params["limit"] == "3"


async def test_suggest_properties_request(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("suggest_properties.json"))
    results = await client.search.suggest_properties("instance", language="en")
    assert results
    assert (
        last_request(httpx_mock).url.path
        == "/w/rest.php/wikibase/v1/suggest/properties"
    )


async def test_suggest_blank_query_rejected(client, httpx_mock):
    with pytest.raises(ConfigurationError, match="non-empty"):
        await client.search.suggest_items("  ")
    assert not httpx_mock.get_requests()


async def test_lexeme_get_routes_and_parses(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("lexeme_l2.json"))
    lexeme = await client.lexemes.get("L2")
    assert lexeme.lemmas["en"] == "first"
    assert lexeme.lexical_category == "Q1084"
    assert lexeme.language == "Q1860"
    form = lexeme.forms[0]
    assert form.representations["en"] == "firsts"
    assert form.grammatical_features == ["Q146786"]
    assert lexeme.senses[0].glosses["en"].startswith("Element in an ordered list")
    assert (
        last_request(httpx_mock).url.path
        == "/w/rest.php/wikibaselexeme/v0/entities/lexemes/L2"
    )


async def test_lexeme_non_lexeme_id_rejected(client, httpx_mock):
    with pytest.raises(Exception, match="lexeme id"):
        await client.lexemes.get("Q42")
    assert not httpx_mock.get_requests()


async def test_available_badges(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("badges.json"))
    badges = await client.utilities.available_badges()
    assert "Q17437798" in badges
    params = last_params(httpx_mock)
    assert params["action"] == "wbavailablebadges"
    assert params["format"] == "json"


async def test_format_entities(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("format_entities.json"))
    links = await client.utilities.format_entities(["Q42", "P31"])
    assert links["P31"].startswith("<a ")
    assert last_params(httpx_mock)["ids"] == "Q42|P31"


async def test_format_entities_requires_ids(client, httpx_mock):
    with pytest.raises(ConfigurationError):
        await client.utilities.format_entities([])
    assert not httpx_mock.get_requests()


async def test_format_value(client, httpx_mock):
    httpx_mock.add_response(json={"result": "hello"})
    result = await client.utilities.format_value(
        {"type": "string", "value": "hello"}, "string"
    )
    assert result == "hello"
    params = last_params(httpx_mock)
    assert params["datatype"] == "string"
    assert '"type"' in params["datavalue"]


async def test_parse_value(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("parse_value.json"))
    parsed = await client.utilities.parse_value(["Q42"], datatype="wikibase-item")
    assert parsed[0].raw == "Q42"
    assert parsed[0].type == "wikibase-entityid"
    assert parsed[0].value["id"] == "Q42"
    params = last_params(httpx_mock)
    assert params["action"] == "wbparsevalue"
    assert params["values"] == "Q42"


async def test_suggestions_by_properties(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("suggestions.json"))
    suggestions = await client.utilities.suggestions(properties=["P31"], limit=2)
    assert suggestions[0].id == "P17"
    assert suggestions[0].rating
    params = last_params(httpx_mock)
    assert params["action"] == "wbsgetsuggestions"
    assert params["properties"] == "P31"
    assert params["limit"] == "2"


async def test_suggestions_requires_entity_or_properties(client, httpx_mock):
    with pytest.raises(ConfigurationError, match="entity= or properties="):
        await client.utilities.suggestions()
    assert not httpx_mock.get_requests()


async def test_check_constraints(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("check_constraints.json"))
    report = await client.utilities.check_constraints(["Q42"])
    checks = next(items for items in report["Q42"].values())
    assert checks[0].id.startswith("Q42$")
    assert checks[0].mainsnak.results[0].status == "bad-parameters"
    assert checks[0].mainsnak.results[0].constraint.type == "Q21502404"
    assert last_params(httpx_mock)["id"] == "Q42"
    assert "entityid" not in last_params(httpx_mock)
