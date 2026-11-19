"""Tests for CrossrefUnwrapper."""


def test_unwrap_results(unwrapper):
    data = {"message": {"total-results": 2, "items": [{"DOI": "1"}, {"DOI": "2"}]}}
    assert unwrapper.unwrap_results(data) == [{"DOI": "1"}, {"DOI": "2"}]


def test_unwrap_results_missing_message(unwrapper):
    assert unwrapper.unwrap_results({}) == []


def test_unwrap_results_missing_items(unwrapper):
    assert unwrapper.unwrap_results({"message": {"total-results": 0}}) == []


def test_unwrap_results_message_not_dict(unwrapper):
    """Error envelopes carry a list-valued message; results must be []."""
    assert unwrapper.unwrap_results({"message": [{"type": "validation-failure"}]}) == []


def test_unwrap_single_item(unwrapper):
    data = {"message": {"DOI": "10.1038/x", "title": ["Test"]}}
    assert unwrapper.unwrap_single_item(data) == {"DOI": "10.1038/x", "title": ["Test"]}


def test_unwrap_single_item_missing_message(unwrapper):
    assert unwrapper.unwrap_single_item({}) == {}


def test_get_next_page_token(unwrapper):
    data = {"message": {"next-cursor": "MTAyNzU1NjE0MzAwMA=="}}
    assert unwrapper.get_next_page_token(data) == "MTAyNzU1NjE0MzAwMA=="


def test_get_next_page_token_none(unwrapper):
    assert unwrapper.get_next_page_token({}) is None
    assert unwrapper.get_next_page_token({"message": {}}) is None


def test_get_total_results(unwrapper):
    assert unwrapper.get_total_results({"message": {"total-results": 42}}) == 42


def test_get_total_results_none(unwrapper):
    assert unwrapper.get_total_results({}) is None
    assert unwrapper.get_total_results({"message": {}}) is None


def test_get_total_results_string(unwrapper):
    assert unwrapper.get_total_results({"message": {"total-results": "42"}}) == 42
