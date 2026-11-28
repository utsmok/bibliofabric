"""Outgoing request shape: paths, parameters, batching, paging, guards."""

import pytest
from bibliofabric.exceptions import ConfigurationError, NotFoundError
from quiddita import QuidditaClient

from ..conftest import (
    claim_record,
    entities_envelope,
    entity,
    load_fixture,
    rest_item,
    rest_statement,
    search_envelope,
    search_result,
    sparql_envelope,
)

ENTITY_Q42 = load_fixture("entity_q42.json")
LABELS = load_fixture("entity_labels.json")
SEARCH = load_fixture("search_entities.json")
CLAIMS = load_fixture("claims_p569.json")
ERROR_IDS = load_fixture("error_too_many_ids.json")
ERROR_MISSING = load_fixture("error_no_such_entity.json")
REST_ITEM = load_fixture("rest_item_q42.json")
REST_STATEMENT = load_fixture("rest_statement.json")
REST_SEARCH = load_fixture("rest_search_items.json")
REST_DATATYPES = load_fixture("rest_property_data_types.json")
UNKNOWN_ID_ERROR = {
    "error": {
        "code": "no-such-entity",
        "info": 'Could not find an entity with the ID "Q999999999999".',
        "id": "Q999999999999",
    }
}


def last_request(httpx_mock):
    return httpx_mock.get_requests()[-1]


def last_params(httpx_mock) -> dict[str, str]:
    return dict(last_request(httpx_mock).url.params)


def add_entities(client: QuidditaClient, httpx_mock, records: list[dict]):
    httpx_mock.add_response(json=entities_envelope(*records))


async def test_get_sends_action_api_params(client, httpx_mock):
    add_entities(client, httpx_mock, [entity()])
    result = await client.entities.get("Q42")
    assert result.id == "Q42"
    params = last_params(httpx_mock)
    assert last_request(httpx_mock).url.path == "/w/api.php"
    assert params["action"] == "wbgetentities"
    assert params["ids"] == "Q42"
    assert params["format"] == "json"


async def test_get_normalizes_url_forms(client, httpx_mock):
    add_entities(client, httpx_mock, [entity()])
    await client.entities.get("https://www.wikidata.org/wiki/Q42")
    assert last_params(httpx_mock)["ids"] == "Q42"


async def test_get_forwards_props_languages_sitefilter_redirects(client, httpx_mock):
    add_entities(client, httpx_mock, [entity()])
    await client.entities.get(
        "Q42",
        select=["labels", "descriptions"],
        params={"languages": ["en", "nl"], "sitefilter": ["enwiki"], "redirects": "no"},
    )
    params = last_params(httpx_mock)
    assert params["props"] == "labels|descriptions"
    assert params["languages"] == "en|nl"
    assert params["sitefilter"] == "enwiki"
    assert params["redirects"] == "no"


async def test_get_missing_entity_raises_not_found(client, httpx_mock):
    httpx_mock.add_response(json=ERROR_MISSING)
    with pytest.raises(NotFoundError):
        await client.entities.get("Q99999999999999")


async def test_get_missing_lexeme_stub_raises_not_found(client, httpx_mock):
    httpx_mock.add_response(json=entities_envelope({"id": "L999999999", "missing": ""}))
    with pytest.raises(NotFoundError, match="L999999999"):
        await client.entities.get("L999999999")


async def test_batch_get_unknown_id_raises_not_found(client, httpx_mock):
    httpx_mock.add_response(json=UNKNOWN_ID_ERROR)
    with pytest.raises(NotFoundError, match="Q999999999999"):
        await client.entities.batch_get(["Q42", "Q999999999999"])
    httpx_mock.add_response(
        json=entities_envelope(entity(), {"id": "L9", "missing": ""})
    )
    with pytest.raises(NotFoundError, match="L9"):
        await client.entities.batch_get(["Q42", "L9"])


async def test_iterate_ids_unknown_id_raises_by_default(client, httpx_mock):
    httpx_mock.add_response(json=UNKNOWN_ID_ERROR)
    with pytest.raises(NotFoundError):
        [
            record
            async for record in client.entities.iterate_ids(["Q42", "Q999999999999"])
        ]


async def test_iterate_ids_skip_retries_without_rejected_id(client, httpx_mock):
    httpx_mock.add_response(json=UNKNOWN_ID_ERROR)
    add_entities(client, httpx_mock, [entity()])
    failures: list = []
    result = [
        record
        async for record in client.entities.iterate_ids(
            ["Q42", "Q999999999999", "Q42"], on_error="skip", failures=failures
        )
    ]
    assert [item.id for item in result] == ["Q42"]
    requests = httpx_mock.get_requests()
    assert [request.url.params["ids"] for request in requests] == [
        "Q42|Q999999999999",
        "Q42",
    ]
    assert [failure[0] for failure in failures] == [{"id": "Q999999999999"}]
    assert isinstance(failures[0][1], NotFoundError)


async def test_iterate_ids_skip_records_missing_stub(client, httpx_mock):
    add_entities(client, httpx_mock, [entity(), {"id": "L999999999", "missing": ""}])
    failures: list = []
    result = [
        record
        async for record in client.entities.iterate_ids(
            ["Q42", "L999999999"], on_error="skip", failures=failures
        )
    ]
    assert [item.id for item in result] == ["Q42"]
    assert [failure[0] for failure in failures] == [{"id": "L999999999", "missing": ""}]
    assert isinstance(failures[0][1], NotFoundError)


async def test_error_body_raises_configuration_error(client, httpx_mock):
    httpx_mock.add_response(json=ERROR_IDS)
    with pytest.raises(ConfigurationError, match="toomanyvalues"):
        await client.entities.get("Q42")


async def test_batch_get_chunks_at_50_ids(client, httpx_mock):
    ids = [f"Q{index}" for index in range(1, 61)]
    for chunk_start in range(0, 60, 50):
        chunk = ids[chunk_start : chunk_start + 50]
        add_entities(client, httpx_mock, [entity(id) for id in chunk])
    result = await client.entities.batch_get(ids)
    assert len(result) == 60
    requests = httpx_mock.get_requests()
    assert len(requests) == 2
    first_ids = requests[0].url.params["ids"].split("|")
    assert len(first_ids) == 50
    assert first_ids == ids[:50]


async def test_iterate_ids_yields_in_order(client, httpx_mock):
    ids = ["Q3", "Q1", "Q2"]
    add_entities(client, httpx_mock, [entity("Q3"), entity("Q1"), entity("Q2")])
    result = [record.id async for record in client.entities.iterate_ids(ids)]
    assert result == ids
    assert last_params(httpx_mock)["ids"] == "Q3|Q1|Q2"


async def test_iterate_ids_skips_unknown_ids(client, httpx_mock):
    add_entities(client, httpx_mock, [entity("Q1")])
    result = [
        record.id async for record in client.entities.iterate_ids(["Q1", "Q999999999"])
    ]
    assert result == ["Q1"]


async def test_search_sends_wbsearchentities_defaults(client, httpx_mock):
    httpx_mock.add_response(json=SEARCH)
    page = await client.search.search(query="douglas adams")
    assert "Q42" in [hit.id for hit in page.results]
    params = last_params(httpx_mock)
    assert params["action"] == "wbsearchentities"
    assert params["search"] == "douglas adams"
    assert params["language"] == "en"
    assert params["continue"] == "0"


async def test_search_options_and_page(client, httpx_mock):
    httpx_mock.add_response(json=SEARCH)
    await client.search.search(
        query="douglas",
        language="nl",
        uselang="nl",
        type="property",
        page=2,
        page_size=10,
    )
    params = last_params(httpx_mock)
    assert params["language"] == "nl"
    assert params["uselang"] == "nl"
    assert params["type"] == "property"
    assert params["limit"] == "10"
    assert params["continue"] == "10"


async def test_search_iterate_walks_continue_offset(client, httpx_mock):
    first = search_envelope([search_result("Q1", "a")], offset=0)
    second = search_envelope([search_result("Q2", "b")], offset=1)
    empty = search_envelope([], offset=2)
    httpx_mock.add_response(json=first)
    httpx_mock.add_response(json=second)
    httpx_mock.add_response(json=empty)
    result = [
        hit.id async for hit in client.search.iterate(query="douglas", page_size=1)
    ]
    assert result == ["Q1", "Q2"]
    offsets = [
        dict(request.url.params).get("continue")
        for request in httpx_mock.get_requests()
    ]
    assert offsets == ["0", "1", "2"]


async def test_search_count_is_unsupported(client):
    with pytest.raises(ConfigurationError, match="does not report a total"):
        await client.search.count(query="douglas")


async def test_rest_search_items(client, httpx_mock):
    httpx_mock.add_response(json=REST_SEARCH)
    results = await client.search.search_items("Douglas Adams", limit=3)
    assert results[0].id == "Q42"
    assert last_request(httpx_mock).url.path == "/w/rest.php/wikibase/v1/search/items"
    assert last_params(httpx_mock)["q"] == "Douglas Adams"


async def test_rest_search_properties(client, httpx_mock):
    httpx_mock.add_response(json=REST_SEARCH)
    results = await client.search.search_properties("instance", language="de")
    assert last_params(httpx_mock)["language"] == "de"
    assert results[0].display_label.value


async def test_claims_get_sends_filters(client, httpx_mock):
    httpx_mock.add_response(json=CLAIMS)
    claims = await client.claims.get("Q42", property="P569", rank="preferred")
    assert claims["P569"][0].mainsnak.property == "P569"
    params = last_params(httpx_mock)
    assert params["action"] == "wbgetclaims"
    assert params["entity"] == "Q42"
    assert params["property"] == "P569"
    assert params["rank"] == "preferred"


async def test_claims_get_invalid_rank_is_rejected_locally(client, httpx_mock):
    with pytest.raises(ConfigurationError, match="rank must be one of"):
        await client.claims.get("Q42", rank="valid")
    assert not httpx_mock.get_requests()


async def test_claims_empty_answer(client, httpx_mock):
    httpx_mock.add_response(json={"claims": {}})
    assert await client.claims.get("Q42") == {}


async def test_sitelinks_get_sends_sitefilter_and_urls(client, httpx_mock):
    item = entity()
    item["sitelinks"] = {"enwiki": {"site": "enwiki", "title": "Douglas Adams"}}
    add_entities(client, httpx_mock, [item])
    links = await client.sitelinks.get(
        "Q42", sites=["enwiki", "dewiki"], with_urls=True
    )
    assert links["enwiki"].title == "Douglas Adams"
    params = last_params(httpx_mock)
    assert params["props"] == "sitelinks/urls"
    assert params["sitefilter"] == "enwiki|dewiki"


async def test_rest_item_get_and_label_routes(client, httpx_mock):
    httpx_mock.add_response(json=REST_ITEM)
    item = await client.items.get("Q42")
    assert item.id == "Q42"
    assert item.sitelinks["enwiki"].url == "https://en.wikipedia.org/wiki/Douglas_Adams"
    httpx_mock.add_response(json={"language": "en", "value": "fallback"})
    term = await client.items.label_with_fallback("Q42", "simple")
    assert term == "fallback"
    assert (
        last_request(httpx_mock).url.path
        == "/w/rest.php/wikibase/v1/entities/items/Q42/labels_with_language_fallback/simple"
    )


async def test_rest_sitelink_route(client, httpx_mock):
    httpx_mock.add_response(
        json={
            "title": "Douglas Adams",
            "badges": ["Q17437798"],
            "url": "https://en.wikipedia.org/wiki/Douglas_Adams",
        }
    )
    link = await client.items.sitelink("Q42", "enwiki")
    assert link.title == "Douglas Adams"
    assert (
        last_request(httpx_mock).url.path
        == "/w/rest.php/wikibase/v1/entities/items/Q42/sitelinks/enwiki"
    )


async def test_rest_property_and_datatypes(client, httpx_mock):
    httpx_mock.add_response(json=rest_item("P31", type="property", datatype="item"))
    httpx_mock.add_response(json=REST_DATATYPES)
    prop = await client.properties.get("P31")
    assert prop.datatype == "item"
    types = await client.properties.datatypes()
    assert types["wikibase-item"] == "wikibase-entityid"


async def test_rest_statements_for_entity_and_property(client, httpx_mock):
    statement = rest_statement("Q42$abc", "P31", "Q5")
    httpx_mock.add_response(json={"P31": [statement]})
    result = await client.statements.for_entity("Q42", property="P31")
    assert result["P31"][0].value.content == "Q5"
    assert (
        last_request(httpx_mock).url.path
        == "/w/rest.php/wikibase/v1/entities/items/Q42/statements"
    )
    httpx_mock.add_response(json={"P31": [statement]})
    await client.statements.for_entity("P31")
    assert last_request(httpx_mock).url.path.endswith(
        "entities/properties/P31/statements"
    )


async def test_rest_statement_by_id_is_quoted(client, httpx_mock):
    httpx_mock.add_response(json=REST_STATEMENT)
    statement = await client.statements.get(REST_STATEMENT["id"])
    assert statement.rank == "normal"
    assert "$" in last_request(httpx_mock).url.path


async def test_rest_statement_id_requires_dollar(client):
    with pytest.raises(ValueError, match="statement id"):
        await client.statements.get("Q42")


async def test_sparql_get_request_shape(client, httpx_mock):
    httpx_mock.add_response(json=sparql_envelope([]))
    result = await client.sparql.query("SELECT ?item WHERE { ?item wdt:P31 wd:Q5 }")
    assert result.head.vars == ["item"]
    request = last_request(httpx_mock)
    assert str(request.url).startswith("https://query.wikidata.org/sparql")
    assert request.method == "GET"
    assert request.url.params["format"] == "json"


async def test_sparql_post_uses_body_and_retry(client, httpx_mock):
    httpx_mock.add_response(
        json=sparql_envelope([{"item": {"type": "uri", "value": "http://x/Q1"}}])
    )
    result = await client.sparql.query_post(
        "SELECT ?item WHERE { ?item wdt:P31 wd:Q5 }"
    )
    assert result.rows() == [{"item": "http://x/Q1"}]
    request = last_request(httpx_mock)
    assert request.method == "POST"
    assert dict(request.url.params).get("query") is None
    assert "query=SELECT" in request.content.decode()


async def test_sparql_query_text_passes_through(client, httpx_mock):
    httpx_mock.add_response(text="a,b\nQ1\n", headers={"content-type": "text/csv"})
    body = await client.sparql.query_text(
        "SELECT ?item WHERE { ?item wdt:P31 wd:Q5 }", format="csv"
    )
    assert body.startswith("a,b")
    request = last_request(httpx_mock)
    assert request.headers["accept"] == "text/csv"
    assert "format" not in request.url.params


async def test_sparql_blank_query_rejected(client, httpx_mock):
    with pytest.raises(ConfigurationError, match="non-empty"):
        await client.sparql.query("   ")
    assert not httpx_mock.get_requests()


async def test_both_hosts_share_one_limiter(client):
    assert client.sparql._client._limiter is client._limiter


async def test_claim_helpers_expose_models(client, httpx_mock):
    add_entities(client, httpx_mock, [entity(claims={"P31": [claim_record()]})])
    result = await client.entities.get("Q42")
    assert result.claims["P31"][0].mainsnak.datavalue.value["numeric-id"] == 5
