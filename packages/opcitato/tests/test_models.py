"""Pydantic models: rows from the real API validate, properties parse ids."""

import pytest
from opcitato import Citation, Count, MetadataRecord
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
