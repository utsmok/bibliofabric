"""Safe typed fields, identifier normalizers, settings, redaction, and dialects."""

import pytest
from bibliofabric.config import BaseApiSettings
from bibliofabric.exceptions import ConfigurationError
from bibliofabric.ids import (
    is_doi,
    normalize_doi,
    normalize_issn,
    normalize_orcid,
    normalize_ror,
    strip_url_prefix,
)
from bibliofabric.paging import QueryDialect
from bibliofabric.types import SafeList, SafeStr
from bibliofabric.utils import sanitize_headers, sanitize_url
from pydantic import BaseModel, Field, ValidationError as PydanticValidationError


class Lists(BaseModel):
    tags: SafeList[str] = Field(default_factory=list)
    name: SafeStr = ""


def test_safe_list_wraps_scalar_string():
    assert Lists.model_validate({"tags": "abc"}).tags == ["abc"]


def test_safe_list_strips_nulls_and_handles_none():
    assert Lists.model_validate({"tags": ["a", None, "b"]}).tags == ["a", "b"]
    assert Lists.model_validate({"tags": None}).tags == []
    assert Lists.model_validate({}).tags == []


def test_safe_list_rejects_dict_and_non_string_scalar():
    with pytest.raises(PydanticValidationError):
        Lists.model_validate({"tags": {"a": "b"}})
    with pytest.raises(PydanticValidationError):
        Lists.model_validate({"tags": 123})


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
    assert (
        normalize_orcid("https://orcid.org/0000-0002-1825-0097/")
        == "0000-0002-1825-0097"
    )
    assert normalize_orcid("000000021825009x") == "0000-0002-1825-009X"
    assert normalize_orcid("orcid:0000-0002-1825-0097") == "0000-0002-1825-0097"
    # Arbitrary 16-char non-ORCID strings must not be hyphenated.
    assert normalize_orcid("abcdefghijklmnop") == "abcdefghijklmnop"


def test_normalize_ror():
    assert normalize_ror("https://ror.org/0524b2x58") == "0524b2x58"
    assert normalize_ror("https://ror.org/0524b2x58/") == "0524b2x58"
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


def test_sanitize_url_and_headers():
    assert (
        sanitize_url("https://api.test/w?mailto=a@b.org&api_key=sec&token=tok")
        == "https://api.test/w?mailto=a@b.org&api_key=***&token=***"
    )
    redacted = sanitize_headers(
        {
            "Authorization": "Bearer abc",
            "X-Api-Key": "secret",
            "Cookie": "sid=xyz",
            "User-Agent": "bibliofabric/0.6.0",
        }
    )
    assert redacted == {
        "Authorization": "***",
        "X-Api-Key": "***",
        "Cookie": "***",
        "User-Agent": "bibliofabric/0.6.0",
    }


def test_settings_constraints_and_user_agent():
    assert (
        BaseApiSettings(user_agent="my-app/1.0").effective_user_agent() == "my-app/1.0"
    )
    ua = BaseApiSettings(mailto="dev@example.org").effective_user_agent()
    assert ua.startswith("bibliofabric/")
    assert "mailto:dev@example.org" in ua
    assert BaseApiSettings(rate_limits={"fast": None, "slow": 1.0}).rate_limits == {
        "fast": None,
        "slow": 1.0,
    }
    for invalid in (
        {"timeout": 0},
        {"timeout": float("inf")},
        {"max_retries": -1},
        {"max_retry_wait": -1},
        {"max_concurrency": 0},
        {"max_requests_per_second": 0},
        {"rate_limits": {"list": 0}},
        {"rate_limits": {"list": float("nan")}},
    ):
        with pytest.raises(PydanticValidationError):
            BaseApiSettings.model_validate(invalid)


def test_query_dialect_invariants():
    with pytest.raises(ConfigurationError):
        QueryDialect(page_size_param="size", max_page_size=0)
    with pytest.raises(ConfigurationError):
        QueryDialect(page_size_param="size", max_page_size=10, default_page_size=20)
    with pytest.raises(ConfigurationError):
        QueryDialect(
            page_size_param="size",
            max_page_size=10,
            default_page_size=5,
            iterate_page_size=11,
        )
    with pytest.raises(ConfigurationError):
        QueryDialect(
            page_size_param="size",
            max_page_size=10,
            default_page_size=5,
            count_page_size=-1,
        )
    assert (
        QueryDialect(
            page_size_param="size",
            max_page_size=10,
            default_page_size=5,
            count_page_size=0,
        ).count_page_size
        == 0
    )
