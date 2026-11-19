"""Safe typed fields, identifier normalizers, and the User-Agent default."""

from pydantic import BaseModel

from bibliofabric.ids import (
    is_doi,
    normalize_doi,
    normalize_issn,
    normalize_orcid,
    normalize_ror,
    strip_url_prefix,
)
from bibliofabric.types import SafeList, SafeStr


class Lists(BaseModel):
    tags: SafeList[str] = []
    name: SafeStr = ""


def test_safe_list_wraps_scalar_string():
    assert Lists.model_validate({"tags": "abc"}).tags == ["abc"]


def test_safe_list_strips_nulls_and_handles_none():
    assert Lists.model_validate({"tags": ["a", None, "b"]}).tags == ["a", "b"]
    assert Lists.model_validate({"tags": None}).tags == []
    assert Lists.model_validate({}).tags == []


def test_safe_str_coerces_none():
    assert Lists.model_validate({"name": None}).name == ""


def test_normalize_doi():
    assert normalize_doi("https://doi.org/10.1234/ABC.def") == "10.1234/abc.def"
    assert normalize_doi("http://dx.doi.org/10.1234/x") == "10.1234/x"
    assert normalize_doi("doi:10.1234/x") == "10.1234/x"
    assert normalize_doi("  10.1234/X ") == "10.1234/x"


def test_is_doi():
    assert is_doi("10.1234/abc")
    assert is_doi("https://doi.org/10.1234/abc")
    assert not is_doi("https://example.com/10.1234/abc")
    assert not is_doi("not-a-doi")


def test_normalize_orcid():
    assert (
        normalize_orcid("https://orcid.org/0000-0002-1825-0097")
        == "0000-0002-1825-0097"
    )
    assert normalize_orcid("0000000218250097") == "0000-0002-1825-0097"
    assert normalize_orcid("orcid:0000-0002-1825-0097") == "0000-0002-1825-0097"


def test_normalize_ror():
    assert normalize_ror("https://ror.org/0524b2x58") == "0524b2x58"
    assert normalize_ror("ror:0524B2X58") == "0524b2x58"


def test_normalize_issn():
    assert normalize_issn("20493630") == "2049-3630"
    assert normalize_issn("2049-3630") == "2049-3630"
    assert normalize_issn("2049363x") == "2049-363X"


def test_strip_url_prefix():
    assert (
        strip_url_prefix("https://openalex.org/W1", ["https://openalex.org/"]) == "W1"
    )
    assert strip_url_prefix("W1", ["https://openalex.org/"]) == "W1"
