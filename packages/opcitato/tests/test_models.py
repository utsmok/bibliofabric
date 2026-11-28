"""Pydantic models: rows from the real API validate, properties parse ids."""

import pytest
from opcitato import Citation, Count, MetadataRecord, SparqlResult
from pydantic import ValidationError

from .conftest import citation, count_rows, load_fixture_json, metadata_row


def test_citation_row_of_the_live_api_validates():
    row = Citation.model_validate(load_fixture_json("citation.json")[0])
    assert row.oci == "06101801781-06180334099"
    assert row.journal_sc == "no"


def test_citation_identifiers_parse_citing_and_cited():
    row = Citation.model_validate(citation())
    assert row.citing_identifiers[0].scheme == "omid"
    assert row.cited_identifiers[1].value == "10.1108/jd-12-2013-0166"


def test_citation_keeps_partial_dates_and_negative_timespans():
    row = Citation.model_validate(citation(creation="2025", timespan="-P1Y1M16D"))
    assert row.creation == "2025"
    assert row.timespan == "-P1Y1M16D"


def test_citation_rejects_missing_oci():
    with pytest.raises(ValidationError):
        Citation.model_validate({"citing": "doi:1", "cited": "doi:2"})


def test_count_coerces_the_string_number():
    row = Count.model_validate(count_rows(1806)[0])
    assert row.count == 1806
    assert isinstance(row.count, int)


@pytest.mark.parametrize("value", ["abc", None])
def test_count_rejects_non_numbers(value):
    with pytest.raises(ValidationError):
        Count.model_validate({"count": value})


def test_metadata_row_of_the_live_api_validates():
    row = MetadataRecord.model_validate(load_fixture_json("metadata.json")[0])
    assert row.title == "Adaptive Environmental Management"
    assert row.type == "book"
    assert row.identifiers[0].scheme == "doi"
    assert row.editors == [
        "Allan, Catherine [orcid:0000-0003-2098-4759 omid:ra/069012996]",
        "Stankey, George H. [omid:ra/061808486861]",
    ]


def test_metadata_authors_split_on_semicolons():
    row = MetadataRecord.model_validate(
        metadata_row(author="Peroni, Silvio [orcid:1]; Dutton, Alexander [orcid:2]")
    )
    assert len(row.authors) == 2
    assert row.authors[1] == "Dutton, Alexander [orcid:2]"


def test_metadata_empty_strings_become_defaults():
    row = MetadataRecord.model_validate({"id": "omid:br/1", "author": ""})
    assert row.authors == []
    assert row.title == ""


def test_rows_keep_the_fields_the_models_do_not_name():
    row = Citation.model_validate(citation(data_source="crossref"))
    assert row.model_extra == {"data_source": "crossref"}
    record = MetadataRecord.model_validate(metadata_row(oa_url="https://example.org"))
    assert record.model_extra == {"oa_url": "https://example.org"}


def test_sparql_results_of_the_live_endpoints_validate():
    index = SparqlResult.model_validate(load_fixture_json("sparql_index.json"))
    assert index.rows() == [
        {
            "ci": "https://w3id.org/oc/index/ci/0601-061203747253",
            "citing": "https://w3id.org/oc/meta/br/0601",
            "cited": "https://w3id.org/oc/meta/br/061203747253",
        },
        {
            "ci": "https://w3id.org/oc/index/ci/0601-061203747376",
            "citing": "https://w3id.org/oc/meta/br/0601",
            "cited": "https://w3id.org/oc/meta/br/061203747376",
        },
    ]
    assert index.meta["result-size-total"] == 2

    meta = SparqlResult.model_validate(load_fixture_json("sparql_meta.json"))
    assert meta.results is not None
    term = meta.results.bindings[0]["date"]
    assert term.type == "literal"
    assert term.value == "1999-10"
    assert term.datatype == "http://www.w3.org/2001/XMLSchema#gYearMonth"
    assert term.xml_lang is None


def test_sparql_ask_answer_has_a_boolean_and_no_bindings():
    ask = SparqlResult.model_validate(load_fixture_json("sparql_ask.json"))
    assert ask.boolean is True
    assert ask.head.vars == []
    assert ask.results is None
    assert ask.rows() == []


def test_sparql_language_tag_reads_the_colon_key():
    ask = SparqlResult.model_validate(
        {
            "head": {"vars": ["label"]},
            "results": {
                "bindings": [
                    {"label": {"type": "literal", "value": "Titel", "xml:lang": "de"}}
                ]
            },
        }
    )
    assert ask.results is not None
    assert ask.results.bindings[0]["label"].xml_lang == "de"
