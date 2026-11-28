"""Query builders and the unwrapper, without I/O."""

import pytest
from diurnalia import (
    ConfigurationError,
    DiurnaliaUnwrapper,
    doi_query,
    issn_query,
)

from .conftest import envelope


def test_issn_query_normalizes_and_groups():
    assert issn_query("1932-6203") == "issn:1932-6203"
    assert issn_query("19326203") == "issn:1932-6203"


def test_doi_query_accepts_urls_and_strips_prefixes():
    assert doi_query("10.3389/fpubh.2020.00115") == "doi:10.3389/fpubh.2020.00115"
    assert (
        doi_query("https://doi.org/10.3389/fpubh.2020.00115")
        == "doi:10.3389/fpubh.2020.00115"
    )


@pytest.mark.parametrize("blank", ["", "   "])
def test_blank_identifiers_are_rejected(blank):
    with pytest.raises(ConfigurationError, match="non-empty|recognizable"):
        issn_query(blank)
    with pytest.raises(ConfigurationError, match="non-empty|recognizable"):
        doi_query(blank)


def test_unwrapper_reads_results_total_and_meta():
    body = envelope([{"id": "a"}, {"id": "b"}], total=41, page=2, page_size=50)
    unwrapper = DiurnaliaUnwrapper()
    assert unwrapper.results(body) == [{"id": "a"}, {"id": "b"}]
    assert unwrapper.total(body) == 41
    assert unwrapper.meta(body)["page"] == 2
    assert unwrapper.meta(body)["pageSize"] == 50
    assert "results" not in unwrapper.meta(body)


def test_unwrapper_handles_missing_and_broken_envelopes():
    unwrapper = DiurnaliaUnwrapper()
    assert unwrapper.results({}) == []
    assert unwrapper.results([]) == []
    assert unwrapper.results({"results": ["not-a-dict", {"id": "a"}]}) == [{"id": "a"}]
    assert unwrapper.total({}) is None
    assert unwrapper.item({"id": "a"}) == {"id": "a"}
    assert unwrapper.next_cursor(envelope([])) is None
