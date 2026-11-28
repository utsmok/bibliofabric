"""The CSV parser reads the format=csv tables of both APIs."""

from opcitato import parse_csv_rows

from .conftest import load_fixture


def test_parse_citations_csv_header_and_rows():
    rows = parse_csv_rows(load_fixture("citations.csv"))
    assert list(rows[0]) == [
        "oci",
        "citing",
        "cited",
        "creation",
        "timespan",
        "journal_sc",
        "author_sc",
    ]
    assert rows[0]["oci"] == "06012708740-06180334099"
    assert len(rows) == 4


def test_parse_metadata_csv():
    rows = parse_csv_rows(load_fixture("metadata.csv"))
    assert len(rows) == 1
    assert rows[0]["pub_date"] == "2009"


def test_parse_csv_pads_short_rows_and_drops_long_ones():
    rows = parse_csv_rows("a,b\n1\n1,2,extra\n")
    assert rows == [{"a": "1", "b": ""}, {"a": "1", "b": "2"}]
