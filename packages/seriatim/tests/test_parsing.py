"""Parsing and helper tests with no I/O; run once, not per variant."""

from typing import Any

import pytest
from bibliofabric.exceptions import APIError, ConfigurationError
from seriatim import (
    LangString,
    LtwaEntry,
    SearchHit,
    SearchPage,
    is_valid_issn,
    parse_issn_l,
    parse_issn_record,
    parse_ltwa_page,
    parse_search_page,
    record_issn,
    require_issn,
)

from .conftest import load_fixture, load_json_fixture

NATURE = load_json_fixture("record_print_nature.json")
ONLINE_X = load_json_fixture("record_online_check_digit_x.json")
CANCELLED = load_json_fixture("record_cancelled.json")
ISSN_L = load_json_fixture("issn_l_nature.json")
SEARCH_HTML = load_fixture("search_results.html")
LTWA_HTML = load_fixture("ltwa_rows.html")
LTWA_EMPTY_HTML = load_fixture("ltwa_page_empty.html")


def test_record_keeps_every_typed_field():
    record = parse_issn_record(NATURE)
    assert record.issn == "0028-0836"
    assert record.issn_l == "0028-0836"
    assert record.key_title == "Nature (London)"
    assert record.format == "medium:Print"
    assert record.type_dct == "formofmaterial:a"
    assert record.main_title == "Nature."
    assert record.name == ["Nature.", "Nature"]
    assert record.type == ["bf:Work", "bf:Instance", "schema:Periodical"]
    assert record.has_cancelled_issn_l == []
    assert record.has_incorrect_issn == []
    assert record.spatial[0].endswith("iso:code:3166:GB")
    provenance = record.main_entity_of
    assert provenance is not None
    assert provenance.status == "recordStatus:Register"
    assert provenance.generated_by is not None
    assert provenance.generated_by.was_associated_with == "issnCenter:BO"
    assert provenance.was_attributed_to is not None
    assert provenance.was_attributed_to.id == "issnCenter:_2"
    nodes = record.identified_by
    assert isinstance(nodes, dict)
    assert nodes["#ISSN"].status == "idStatus:Valid"
    assert nodes["#ISSN"].has_cancelled_issn == ["resource:ISSN/0302-2889#ISSN"]
    key_title = nodes["#KeyTitle"].main_title
    assert isinstance(key_title, LangString)
    assert key_title.language == "und-Latn"
    title_objects = [entry for entry in record.title if not isinstance(entry, str)]
    assert title_objects[0].main_title is not None
    assert title_objects[0].main_title.value == "Nature."


def test_record_keeps_unknown_keys_and_raw_node():
    record = parse_issn_record(NATURE)
    extras = record.model_extra
    assert extras is not None
    base = extras["@context"]["@base"]
    assert base.endswith("ISSN/0028-0836")
    assert record.raw == NATURE


def test_record_of_check_digit_x_online_journal():
    record = parse_issn_record(ONLINE_X)
    assert record.issn == "2434-561X"
    assert record.format == "medium:Online"
    assert record.issn_l == "1883-3993"
    assert record.url == ["https://archives.bukkyo-u.ac.jp/baker/cresult.php?code=DK"]


def test_cancelled_record_flat_shape():
    record = parse_issn_record(CANCELLED)
    assert record.issn == "0302-2889"
    assert record.issn_l is None
    assert record.key_title is None
    assert record.main_title is None
    assert record.format is None
    node = record.identified_by
    assert node is not None and not isinstance(node, dict)
    assert node.cancelled_in_favor_of == ["resource:ISSN/0028-0836#ISSN"] * 2
    assert node.status == "idStatus:Cancelled"
    provenance = record.main_entity_of
    assert provenance is not None
    assert provenance.status == "recordStatus:Cancelled"


def test_issn_l_record():
    cluster = parse_issn_l(ISSN_L)
    assert cluster.issn_l == "0028-0836"
    assert cluster.type == ["bf:Instance", "bf:Work"]
    assert [part.identifier for part in cluster.has_part] == [
        "1476-4687",
        "0028-0836",
    ]
    assert [part.format for part in cluster.has_part] == [
        "medium:Online",
        "medium:Print",
    ]
    assert cluster.raw == ISSN_L


def test_record_issn_falls_back_to_identifier():
    record = parse_issn_record(CANCELLED)
    assert record_issn(record) == "0302-2889"


def test_parse_rejects_non_object():
    with pytest.raises(ConfigurationError, match="JSON-LD object"):
        parse_issn_record(["not", "a", "node"])
    with pytest.raises(ConfigurationError, match="JSON-LD object"):
        parse_issn_l(None)


def test_record_issn_raises_without_value():
    bad: Any = {"unexpected-shape": True}
    with pytest.raises(ConfigurationError, match="carries no ISSN"):
        record_issn(parse_issn_record(bad))


def test_is_valid_issn():
    assert is_valid_issn("0028-0836")
    assert is_valid_issn("00280836")
    assert is_valid_issn("2434-561X")
    assert is_valid_issn("2434-561x")
    assert not is_valid_issn("9999-9999")
    assert not is_valid_issn("0028-0835")
    assert not is_valid_issn("not-an-issn")
    assert not is_valid_issn("")


def test_require_issn_normalizes_or_raises():
    assert require_issn("00280836") == "0028-0836"
    assert require_issn(" https://portal.issn.org/resource/ISSN/0028-0836 ") == (
        "0028-0836"
    )
    with pytest.raises(ConfigurationError, match="valid ISSN"):
        require_issn("9999-9999")


def test_parse_search_page_fields():
    page = parse_search_page(SEARCH_HTML, page=1, page_size=20)
    assert isinstance(page, SearchPage)
    assert page.total == 6
    assert page.page == 1
    assert [hit.issn for hit in page.hits] == ["0028-0836", "1476-4687"]
    first = page.hits[0]
    assert isinstance(first, SearchHit)
    assert first.issn_l == "0028-0836"
    assert first.issn_h == "9048-0007"
    assert first.title == "Nature (London)"
    assert first.detail_path == "/resource/ISSN/0028-0836"
    assert first.medium == "ta"
    assert first.medium_label == "Print"
    assert first.country == "GBR"
    assert first.country_label == "UNITED KINGDOM"
    assert first.category == "reg"
    assert first.category_label == "Confirmed record"
    assert first.cancelled_issns == ["0302-2889"]
    assert [medium.label for medium in first.other_media] == ["Online"]
    assert first.other_media[0].href == "/resource/ISSN/1476-4687"
    second = page.hits[1]
    assert second.medium == "cr"
    assert second.medium_label == "Online"
    assert second.issn_l == "0028-0836"
    assert [medium.label for medium in second.other_media] == ["Print"]


def test_parse_search_page_missing_container_raises():
    with pytest.raises(APIError) as error:
        parse_search_page(
            "<html><body>no results markup</body></html>", page=1, page_size=20
        )
    assert "hits" in str(error.value)


def test_parse_ltwa_page():
    entries = parse_ltwa_page(LTWA_HTML)
    assert entries == [
        LtwaEntry(word="Aabenraa", abbreviation=None, language="Danish"),
        LtwaEntry(word="Aachen", abbreviation=None, language="German"),
        LtwaEntry(word="Aachener", abbreviation="Aachen.", language="German"),
        LtwaEntry(word="aakkos-", abbreviation="aakkos.", language="Finnish"),
    ]


def test_parse_ltwa_page_without_table_is_empty():
    assert parse_ltwa_page(LTWA_EMPTY_HTML) == []
