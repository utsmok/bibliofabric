"""Tests for stavrophora._helpers."""

import pytest

from stavrophora._helpers import encode_doi_path, normalize_doi


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("10.1038/nature12373", "10.1038/nature12373"),
        ("  10.1038/Nature12373  ", "10.1038/nature12373"),
        ("https://doi.org/10.1038/nature12373", "10.1038/nature12373"),
        ("http://doi.org/10.1038/nature12373", "10.1038/nature12373"),
        ("doi.org/10.1038/nature12373", "10.1038/nature12373"),
        ("HTTPS://DOI.ORG/10.1038/X", "10.1038/x"),
    ],
)
def test_normalize_doi(raw, expected):
    assert normalize_doi(raw) == expected


def test_encode_doi_path_keeps_slashes():
    assert encode_doi_path("10.1038/Nature12373") == "10.1038/nature12373"


def test_encode_doi_path_encodes_unsafe_characters():
    encoded = encode_doi_path("10.1000/weird#doi?q=1")
    assert "#" not in encoded
    assert "?" not in encoded
    assert encoded == "10.1000/weird%23doi%3Fq%3D1"
