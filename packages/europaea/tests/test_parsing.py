"""Model and helper checks with no I/O (both variants run them once)."""

import pytest
from bibliofabric.exceptions import ConfigurationError
from europaea import (
    Citation,
    GrantRecord,
    ProfileResponse,
    SearchRequest,
    SearchResult,
    split_article_id,
)

from .conftest import (
    citation_record,
    core_record,
    grist_envelope,
    lite_record,
    load_fixture,
)


def test_split_article_id_colon_and_slash():
    assert split_article_id("MED:23903748") == ("MED", "23903748")
    assert split_article_id("PMC/PMC4221854") == ("PMC", "PMC4221854")
    assert split_article_id("ppr/1234") == ("PPR", "1234")


def test_split_article_id_requires_a_source():
    with pytest.raises(ConfigurationError):
        split_article_id("23903748")
    with pytest.raises(ConfigurationError):
        split_article_id("MED:")


def test_lite_record_parses():
    result = SearchResult.model_validate(lite_record())
    assert result.id == "23903748"
    assert result.source == "MED"
    assert result.pub_year == "2013"
    assert result.cited_by_count == 452


def test_core_record_parses_nested_structures():
    result = SearchResult.model_validate(core_record())
    assert result.is_open_access == "Y"
    assert result.journal_info is not None
    assert result.journal_info.journal is not None
    assert result.journal_info.journal.title == "Nature"
    assert result.author_list is not None
    authors = result.author_list.author or []
    author = authors[0]
    assert author.author_id is not None
    assert author.author_id.type == "ORCID"
    assert author.author_id.value == "0000-0002-4189-3154"
    assert result.keyword_list is not None
    assert result.keyword_list.keyword == ["nanodiamond", "thermometry"]


def test_unknown_fields_are_kept():
    result = SearchResult.model_validate(lite_record(someFutureField={"x": 1}))
    assert (result.model_extra or {}).get("someFutureField") == {"x": 1}


def test_search_request_parses_the_echo():
    request = SearchRequest.model_validate(
        {
            "queryString": "cancer",
            "resultType": "core",
            "cursorMark": "*",
            "pageSize": 25,
            "sort": "",
            "synonym": False,
        }
    )
    assert request.query_string == "cancer"
    assert request.page_size == 25
    assert request.synonym is False


def test_citation_record_parses():
    citation = Citation.model_validate(citation_record())
    assert citation.pub_year == 2011

    assert citation.citation_type == "JOURNAL ARTICLE"


def test_grist_record_parses():
    response_records = grist_envelope()
    record = GrantRecord.model_validate(response_records["RecordList"]["Record"][0])
    assert record.person is not None
    assert record.person.family_name == "Asante"
    assert record.grant is not None
    assert record.grant.funder is not None
    assert record.grant.funder.name == "Wellcome Trust"
    assert record.grant.id == "329783"


def test_profile_response_parses():
    profile = ProfileResponse.model_validate(load_fixture("profile.json"))
    assert profile.profile_list is not None
    assert profile.profile_list.source is not None
    counts = {source.name: source.count for source in profile.profile_list.source}
    assert counts["MED"] == 701
