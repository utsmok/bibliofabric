"""Envelope reading and model validation against real fixtures."""

import pytest
from bibliofabric.exceptions import ConfigurationError, NotFoundError
from quiddita import (
    Claim,
    Entity,
    QuidditaUnwrapper,
    SparqlResult,
)

from .conftest import load_fixture

UNWRAPPER = QuidditaUnwrapper()
ENTITY = load_fixture("entity_q42.json")
CLAIMS = load_fixture("claims_p569.json")
SPARQL = load_fixture("sparql_result.json")
ERROR_IDS = load_fixture("error_too_many_ids.json")
ERROR_MISSING = load_fixture("error_no_such_entity.json")
SEARCH = load_fixture("search_entities.json")


def test_item_reads_single_entity():
    record = UNWRAPPER.item(ENTITY)
    assert record["id"] == "Q42"


def test_item_empty_without_entities():
    assert UNWRAPPER.item({"success": 1}) == {}


def test_results_reads_search_hits():
    assert "Q42" in [hit["id"] for hit in UNWRAPPER.results(SEARCH)]


def test_total_is_none():
    assert UNWRAPPER.total(SEARCH) is None


def test_meta_returns_envelope_minus_search():
    meta = UNWRAPPER.meta(SEARCH)
    assert "search" not in meta
    assert "searchinfo" in meta


@pytest.mark.parametrize("body", [ERROR_IDS])
def test_error_body_raises_configuration_error(body: dict):
    with pytest.raises(ConfigurationError, match="Wikidata API rejected"):
        UNWRAPPER.results(body)
    with pytest.raises(ConfigurationError):
        UNWRAPPER.item(body)
    with pytest.raises(ConfigurationError):
        UNWRAPPER.total(body)


def test_no_such_entity_raises_not_found():
    with pytest.raises(NotFoundError, match="no-such-entity"):
        UNWRAPPER.results(ERROR_MISSING)
    with pytest.raises(NotFoundError):
        UNWRAPPER.item(ERROR_MISSING)


def test_entity_model_parses_fixture():
    entity = Entity.model_validate(ENTITY["entities"]["Q42"])
    # Q42 currently has no English label (verified 2026-11-27); the English
    # description answers instead.
    assert entity.label() is None
    assert len(entity.labels) == 75
    assert (
        entity.description()
        == "British science fiction writer and humorist (1952–2001)"
    )
    assert entity.claims["P31"][0].mainsnak.datavalue is not None
    assert entity.claims["P569"][0].rank == "normal"
    assert entity.sitelinks["enwiki"].title == "Douglas Adams"
    reference = entity.claims["P569"][0].references[0]
    assert reference.snaks["P248"][0].datavalue is not None


def test_claim_fixture_parses():
    claims = CLAIMS["claims"]["P569"]
    parsed = Claim.model_validate(claims[0])
    assert parsed.mainsnak.property == "P569"


def test_sparql_result_parses_fixture():
    result = SparqlResult.model_validate(SPARQL)
    assert result.head.vars == ["item", "l"]
    assert result.results.bindings[0]["item"].type == "uri"
    assert result.rows()[0]["item"] == "http://www.wikidata.org/entity/L1742768"
