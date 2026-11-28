"""Pure helpers: the ``q`` clause builders and id normalization."""

import pytest
from zenotheca import (
    ConfigurationError,
    all_of,
    any_of,
    community,
    normalize_community_slug,
    normalize_record_id,
    phrase,
    resource_type,
    term,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("24378467", "24378467"),
        (24378467, "24378467"),
        (" 24378467 ", "24378467"),
        ("10.5281/zenodo.24378467", "24378467"),
        ("https://zenodo.org/records/24378467", "24378467"),
        ("https://zenodo.org/records/24378467?v=1", "24378467"),
        ("https://zenodo.org/api/records/24378467", "24378467"),
        ("https://zenodo.org/record/24378467", "24378467"),
        ("6347574", "6347574"),
    ],
)
def test_normalize_record_id(value, expected):
    assert normalize_record_id(value) == expected


@pytest.mark.parametrize(
    "value",
    ["", "ror-data", "not-an-id", "https://example.org/records/1", "10.1234/abc"],
)
def test_normalize_record_id_rejects_other_values(value):
    with pytest.raises(ConfigurationError):
        normalize_record_id(value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("ror-data", "ror-data"),
        ("https://zenodo.org/communities/ror-data", "ror-data"),
    ],
)
def test_normalize_community_slug(value, expected):
    assert normalize_community_slug(value) == expected


@pytest.mark.parametrize("value", ["", "https://example.org/communities/x", "a/b"])
def test_normalize_community_slug_rejects_other_values(value):
    with pytest.raises(ConfigurationError):
        normalize_community_slug(value)


def test_term_and_phrase():
    assert term("communities", "ror-data") == "communities:ror-data"
    assert phrase("title", "ROR Data") == 'title:"ROR Data"'


def test_term_rejects_reserved_characters():
    with pytest.raises(ConfigurationError, match="phrase"):
        term("title", "ROR Data")
    with pytest.raises(ConfigurationError, match="non-empty"):
        term("title", "  ")


def test_phrase_rejects_quotes_and_empty():
    with pytest.raises(ConfigurationError, match="cannot contain"):
        phrase("title", 'a"b')
    with pytest.raises(ConfigurationError, match="non-empty"):
        phrase("title", "")


def test_clause_combinators():
    assert community("ror-data") == "communities:ror-data"
    assert resource_type("dataset") == "type:dataset"
    assert any_of("a", "b") == "(a OR b)"
    assert any_of("a") == "a"
    assert all_of("a", "b") == "a b"
    with pytest.raises(ConfigurationError):
        any_of()
    with pytest.raises(ConfigurationError):
        all_of()
