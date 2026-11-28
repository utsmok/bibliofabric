"""Live Wikidata smoke tests against the real API (paced, few requests)."""

from collections.abc import Callable
from typing import NoReturn, cast

import pytest
from bibliofabric.exceptions import NotFoundError, RateLimitError
from quiddita import QuidditaClient, QuidditaSettings

pytestmark = pytest.mark.live_api

# The installed pytest type stubs disagree with the runtime signature of
# pytest.skip about its positional argument, so the attribute goes through a
# callable cast.
_skip = cast(Callable[..., NoReturn], pytest.skip)


@pytest.fixture
async def live_client():
    # One retry: a live smoke set should fail fast on 429 instead of
    # spending minutes in backoff.
    async with QuidditaClient(
        settings=QuidditaSettings(_env_file=None, max_retries=1)
    ) as client:
        yield client


async def test_get_entity_smoke(live_client):
    record = await live_client.entities.get("Q42")
    assert record.id == "Q42"
    assert (
        record.description()
        == "British science fiction writer and humorist (1952–2001)"
    )
    assert record.claims["P31"][0].mainsnak.datavalue is not None
    assert record.sitelinks["enwiki"].title == "Douglas Adams"


async def test_get_not_found_smoke(live_client):
    with pytest.raises(NotFoundError):
        await live_client.entities.get("Q99999999999999")


async def test_batch_get_smoke(live_client):
    result = await live_client.entities.batch_get(
        ["Q42", "P31", "https://www.wikidata.org/wiki/L1"], select=["labels"]
    )
    assert set(result) == {"Q42", "P31", "L1"}
    assert result["P31"].label() == "instance of"


async def test_get_missing_lexeme_smoke(live_client):
    with pytest.raises(NotFoundError, match="L999999999"):
        await live_client.entities.get("L999999999")


async def test_iterate_ids_skips_unknown_ids_smoke(live_client):
    failures: list = []
    records = [
        record
        async for record in live_client.entities.iterate_ids(
            ["Q42", "Q999999999999", "L999999999"], on_error="skip", failures=failures
        )
    ]
    assert [record.id for record in records] == ["Q42"]
    assert [failure[0]["id"] for failure in failures] == [
        "Q999999999999",
        "L999999999",
    ]


async def test_search_smoke(live_client):
    page = await live_client.search.search(query="douglas adams", page_size=5)
    assert "Q42" in [hit.id for hit in page.results]
    assert page.total is None


async def test_rest_search_smoke(live_client):
    results = await live_client.search.search_items(
        "Douglas Adams", language="en", limit=2
    )
    assert results[0].id == "Q42"
    assert results[0].display_label.value


async def test_claims_smoke(live_client):
    claims = await live_client.claims.get("Q42", property="P569")
    assert claims["P569"][0].rank == "normal"


async def test_sitelinks_smoke(live_client):
    links = await live_client.sitelinks.get("Q42", sites="enwiki")
    assert links["enwiki"].title == "Douglas Adams"
    assert links["enwiki"].url is None


async def test_sitelinks_with_urls_smoke(live_client):
    links = await live_client.sitelinks.get("Q42", sites="enwiki", with_urls=True)
    assert links["enwiki"].url is not None and "wikipedia.org" in links["enwiki"].url


async def test_rest_items_smoke(live_client):
    item = await live_client.items.get("Q42")
    assert item.id == "Q42"
    assert item.sitelinks["enwiki"].title == "Douglas Adams"
    label = await live_client.items.label_with_fallback("Q42", "simple")
    assert label == "Douglas Adams"


async def test_rest_properties_and_datatypes_smoke(live_client):
    prop = await live_client.properties.get("P31")
    assert prop.id == "P31"
    assert prop.statements["P31"][0].value.type == "value"
    types = await live_client.properties.datatypes()
    assert types["wikibase-item"] == "wikibase-entityid"


async def test_rest_statements_smoke(live_client):
    statements = await live_client.statements.for_entity("Q42", property="P31")
    assert statements["P31"][0].value.content == "Q5"


async def test_sparql_smoke(live_client):
    # One test, three requests: the query service throttles harder than the
    # wiki host, so the smoke set keeps its SPARQL footprint small. Under
    # upstream 429 throttling the test skips instead of failing the gate.
    query = "SELECT ?item WHERE { ?item wdt:P31 wd:Q5 } LIMIT 2"
    try:
        result = await live_client.sparql.query(query)
    except RateLimitError as error:
        reason = f"query service throttled: {error}"
        _skip(reason)
    assert result.head.vars == ["item"]
    assert len(result.results.bindings) == 2
    assert result.rows()[0]["item"].startswith("http")

    posted = await live_client.sparql.query_post(
        "SELECT ?item WHERE { ?item wdt:P31 wd:Q5 } LIMIT 1"
    )
    assert len(posted.results.bindings) == 1

    body = await live_client.sparql.query_text(query, format="csv")
    assert body.splitlines()[0].strip() == "item"


async def test_entity_data_smoke(live_client):
    result = await live_client.entity_data.get("Q42")
    assert result.entity is not None and result.entity.id == "Q42"
    ttl = await live_client.entity_data.get("Q42", format="ttl")
    assert ttl.document is not None
    assert ttl.document.content_type.startswith("text/turtle")
    negotiated = await live_client.entity_data.negotiate("Q42", accept="text/turtle")
    assert negotiated.content_type.startswith("text/turtle")


async def test_suggest_smoke(live_client):
    items = await live_client.search.suggest_items("einstein", language="en", limit=3)
    assert "Q937" in [hit.id for hit in items]
    props = await live_client.search.suggest_properties("instance", language="en")
    assert props and props[0].id.startswith("P")


async def test_lexeme_smoke(live_client):
    lexeme = await live_client.lexemes.get("L2")
    assert lexeme.lemmas["en"] == "first"
    assert lexeme.forms and lexeme.senses


async def test_utilities_smoke(live_client):
    badges = await live_client.utilities.available_badges()
    assert badges
    links = await live_client.utilities.format_entities(["Q42"])
    assert "Q42" in links
    parsed = await live_client.utilities.parse_value(["Q42"], datatype="wikibase-item")
    assert parsed[0].value["id"] == "Q42"
    suggestions = await live_client.utilities.suggestions(properties=["P31"])
    assert suggestions
    report = await live_client.utilities.check_constraints(["Q42"])
    assert report["Q42"]


async def test_shared_limiter_live(live_client):
    assert live_client.sparql._client._limiter is live_client._limiter
