"""Identifier helpers: parsing citing/cited strings, validating path ids."""

import pytest
from opcitato import (
    ParsedIdentifier,
    normalize_index_id,
    normalize_issn,
    normalize_meta_ids,
    normalize_oci,
    normalize_person_id,
    parse_identifiers,
)


def test_parse_identifiers_splits_schemes():
    parsed = parse_identifiers(
        "omid:br/06120344846 doi:10.1038/nature12373 pmid:23903748 openalex:W2159974629"
    )
    assert parsed == [
        ParsedIdentifier("omid", "br/06120344846"),
        ParsedIdentifier("doi", "10.1038/nature12373"),
        ParsedIdentifier("pmid", "23903748"),
        ParsedIdentifier("openalex", "W2159974629"),
    ]
    assert parsed[1].__str__() == "doi:10.1038/nature12373"


def test_parse_identifiers_lowercases_the_scheme():
    parsed = parse_identifiers("DOI:10.1038/nature12373")
    assert parsed == [ParsedIdentifier("doi", "10.1038/nature12373")]


def test_parse_identifiers_of_an_empty_string_is_empty():
    assert parse_identifiers("") == []


@pytest.mark.parametrize("text", ["nonsense", "doi:", ":value", "mid:"])
def test_parse_identifiers_rejects_unprefixed_parts(text):
    with pytest.raises(Exception, match="scheme:value"):
        parse_identifiers(text)


def test_normalize_index_id_accepts_documented_schemes():
    assert normalize_index_id("doi:10.1038/nature12373") == "doi:10.1038/nature12373"
    assert normalize_index_id(" omid:br/06120344846 ") == "omid:br/06120344846"
    assert normalize_index_id("PMID:23903748") == "pmid:23903748"


def test_normalize_index_id_rejects_bare_doi():
    with pytest.raises(Exception, match="scheme:value"):
        normalize_index_id("10.1038/nature12373")


def test_normalize_index_id_rejects_openalex():
    with pytest.raises(Exception, match="openalex"):
        normalize_index_id("openalex:W2159974629")


def test_normalize_index_id_rejects_whitespace():
    with pytest.raises(Exception, match="whitespace"):
        normalize_index_id("doi:10.1 2")


def test_normalize_meta_ids_joins_with_double_underscore():
    assert (
        normalize_meta_ids(["doi:10.1108/jd-12-2013-0166", "doi:10.1016/j.websem"])
        == "doi:10.1108/jd-12-2013-0166__doi:10.1016/j.websem"
    )


def test_normalize_meta_ids_accepts_packed_string():
    assert normalize_meta_ids("doi:a__omid:br/1") == "doi:a__omid:br/1"


def test_normalize_meta_ids_accepts_meta_only_schemes():
    assert normalize_meta_ids("openalex:W2159974629") == "openalex:W2159974629"


def test_normalize_meta_ids_rejects_unknown_scheme():
    with pytest.raises(Exception, match="unsupported scheme"):
        normalize_meta_ids("handle:1234")


def test_normalize_meta_ids_rejects_empty():
    with pytest.raises(Exception, match="non-empty"):
        normalize_meta_ids([])


def test_normalize_person_id_accepts_orcid_and_omid():
    assert (
        normalize_person_id("orcid:0000-0002-8420-0696") == "orcid:0000-0002-8420-0696"
    )
    assert normalize_person_id("omid:ra/0601") == "omid:ra/0601"


def test_normalize_person_id_rejects_document_schemes():
    with pytest.raises(Exception, match="unsupported scheme"):
        normalize_person_id("doi:10.1038/nature12373")


def test_normalize_issn_requires_the_issn_scheme():
    assert normalize_issn("issn:0138-9130") == "issn:0138-9130"
    with pytest.raises(Exception, match="doi"):
        normalize_issn("doi:10.1038/nature12373")


def test_normalize_oci_strips_the_prefix():
    assert normalize_oci("06101801781-06180334099") == "06101801781-06180334099"
    assert normalize_oci("oci:1-18") == "1-18"


@pytest.mark.parametrize("value", ["", "1-18-3", "abc", "oci:abc"])
def test_normalize_oci_rejects_other_shapes(value):
    with pytest.raises(Exception, match="dash"):
        normalize_oci(value)


def test_path_ids_are_percent_encoded_and_keep_their_separators():
    sici = "10.1002/(SICI)1097-4636(199823)43:3<338::AID-JBM16>3.0.CO;2-B"
    assert normalize_index_id(f"doi:{sici}") == (
        "doi:10.1002/%28SICI%291097-4636%28199823%2943:3%3C338::AID-JBM16%3E3.0.CO%3B2-B"
    )
    assert normalize_index_id("doi:10.1000/a#b?c") == "doi:10.1000/a%23b%3Fc"
    assert normalize_index_id(" doi:10.1038/nature12373 ") == "doi:10.1038/nature12373"
    assert normalize_person_id("omid:ra/0601") == "omid:ra/0601"
    assert normalize_meta_ids(["doi:10.1000/a#1", "pmid:12"]) == (
        "doi:10.1000/a%231__pmid:12"
    )
