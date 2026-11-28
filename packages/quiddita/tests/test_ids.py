"""Identifier normalization."""

import pytest
from bibliofabric.exceptions import ConfigurationError
from quiddita import normalize_wikidata_id


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Q42", "Q42"),
        ("q42", "Q42"),
        ("P31", "P31"),
        ("L1", "L1"),
        ("L1-F1", None),
        ("  Q42  ", "Q42"),
        ("https://www.wikidata.org/wiki/Q42", "Q42"),
        ("http://www.wikidata.org/wiki/Q42", "Q42"),
        ("https://www.wikidata.org/entity/P31", "P31"),
        ("https://wikidata.org/entity/L1", "L1"),
        ("https://www.wikidata.org/wiki/Property:P31", None),
    ],
)
def test_normalize(value: str, expected: str | None):
    if expected is None:
        with pytest.raises(ConfigurationError):
            normalize_wikidata_id(value)
    else:
        assert normalize_wikidata_id(value) == expected


def test_rejects_junk():
    with pytest.raises(ConfigurationError, match="Expected a Wikidata id"):
        normalize_wikidata_id("Qabc")


def test_rejects_mediainfo():
    with pytest.raises(ConfigurationError, match="MediaInfo"):
        normalize_wikidata_id("M42")
