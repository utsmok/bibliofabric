import pytest

from aireloom.unwrapper import OpenAireUnwrapper


@pytest.fixture
def unwrapper():
    return OpenAireUnwrapper()


# Tests for unwrap_results
def test_unwrap_results_valid(unwrapper):
    response_json = {"results": [{"id": 1}, {"id": 2}]}
    assert unwrapper.unwrap_results(response_json) == [{"id": 1}, {"id": 2}]


def test_unwrap_results_empty(unwrapper):
    response_json = {"results": []}
    assert unwrapper.unwrap_results(response_json) == []


def test_unwrap_results_missing_key(unwrapper):
    response_json = {}
    assert unwrapper.unwrap_results(response_json) == []


def test_unwrap_results_none_value(unwrapper):
    response_json = {"results": None}
    assert unwrapper.unwrap_results(response_json) == []


def test_unwrap_results_invalid_type(unwrapper):
    response_json = {"results": "not a list"}
    with pytest.raises(ValueError, match="Expected results to be a list"):
        unwrapper.unwrap_results(response_json)


def test_unwrap_results_response_json_none(unwrapper):
    with pytest.raises(ValueError, match="Response JSON cannot be None"):
        unwrapper.unwrap_results(None)


def test_unwrap_results_response_json_not_dict(unwrapper):
    with pytest.raises(ValueError, match="Response JSON must be a dictionary"):
        unwrapper.unwrap_results("not a dict")


# Tests for unwrap_single_item
def test_unwrap_single_item_valid(unwrapper):
    response_json = {"results": [{"id": 1}]}
    assert unwrapper.unwrap_single_item(response_json) == {"id": 1}


def test_unwrap_single_item_multiple_results(unwrapper):
    # Should still return the first item
    response_json = {"results": [{"id": 1}, {"id": 2}]}
    assert unwrapper.unwrap_single_item(response_json) == {"id": 1}


def test_unwrap_single_item_no_results(unwrapper):
    response_json = {"results": []}
    with pytest.raises(ValueError, match="No results found in response for single item request"):
        unwrapper.unwrap_single_item(response_json)


def test_unwrap_single_item_missing_key(unwrapper):
    response_json = {}
    with pytest.raises(ValueError, match="No results found in response for single item request"):
        unwrapper.unwrap_single_item(response_json)

def test_unwrap_single_item_results_none(unwrapper):
    response_json = {"results": None}
    with pytest.raises(ValueError, match="No results found in response for single item request"):
        unwrapper.unwrap_single_item(response_json)


def test_unwrap_single_item_response_json_none(unwrapper):
    with pytest.raises(ValueError, match="Response JSON cannot be None"):
        unwrapper.unwrap_single_item(None)


def test_unwrap_single_item_response_json_not_dict(unwrapper):
    with pytest.raises(ValueError, match="Response JSON must be a dictionary"):
        unwrapper.unwrap_single_item("not a dict")


# Tests for get_next_page_token
def test_get_next_page_token_valid(unwrapper):
    response_json = {"header": {"nextCursor": "cursor123"}}
    assert unwrapper.get_next_page_token(response_json) == "cursor123"


def test_get_next_page_token_whitespace(unwrapper):
    response_json = {"header": {"nextCursor": "  cursor123  "}}
    assert unwrapper.get_next_page_token(response_json) == "cursor123"


def test_get_next_page_token_none(unwrapper):
    response_json = {"header": {"nextCursor": None}}
    assert unwrapper.get_next_page_token(response_json) is None


def test_get_next_page_token_empty_string(unwrapper):
    response_json = {"header": {"nextCursor": ""}}
    assert unwrapper.get_next_page_token(response_json) is None

def test_get_next_page_token_only_whitespace(unwrapper):
    response_json = {"header": {"nextCursor": "   "}}
    assert unwrapper.get_next_page_token(response_json) is None


def test_get_next_page_token_missing_cursor_key(unwrapper):
    response_json = {"header": {}}
    assert unwrapper.get_next_page_token(response_json) is None


def test_get_next_page_token_missing_header_key(unwrapper):
    response_json = {}
    assert unwrapper.get_next_page_token(response_json) is None


def test_get_next_page_token_header_not_dict(unwrapper):
    response_json = {"header": "not a dict"}
    assert unwrapper.get_next_page_token(response_json) is None


def test_get_next_page_token_response_json_not_dict(unwrapper):
    assert unwrapper.get_next_page_token("not a dict") is None

def test_get_next_page_token_cursor_is_int(unwrapper):
    response_json = {"header": {"nextCursor": 123}}
    assert unwrapper.get_next_page_token(response_json) == "123"

def test_get_next_page_token_cursor_is_url_object(unwrapper):
    class URLObject:
        def __str__(self):
            return "http://example.com/cursor"
    response_json = {"header": {"nextCursor": URLObject()}}
    assert unwrapper.get_next_page_token(response_json) == "http://example.com/cursor"

def test_get_next_page_token_cursor_object_str_empty(unwrapper):
    class URLObjectEmpty:
        def __str__(self):
            return ""
    response_json = {"header": {"nextCursor": URLObjectEmpty()}}
    assert unwrapper.get_next_page_token(response_json) is None


# Tests for get_total_results
def test_get_total_results_valid_int(unwrapper):
    response_json = {"header": {"numFound": 100}}
    assert unwrapper.get_total_results(response_json) == 100


def test_get_total_results_valid_string(unwrapper):
    response_json = {"header": {"numFound": "100"}}
    assert unwrapper.get_total_results(response_json) == 100


def test_get_total_results_none(unwrapper):
    response_json = {"header": {"numFound": None}}
    assert unwrapper.get_total_results(response_json) is None


def test_get_total_results_invalid_string(unwrapper):
    response_json = {"header": {"numFound": "abc"}}
    assert unwrapper.get_total_results(response_json) is None


def test_get_total_results_missing_numfound_key(unwrapper):
    response_json = {"header": {}}
    assert unwrapper.get_total_results(response_json) is None


def test_get_total_results_missing_header_key(unwrapper):
    response_json = {}
    assert unwrapper.get_total_results(response_json) is None


def test_get_total_results_header_not_dict(unwrapper):
    response_json = {"header": "not a dict"}
    assert unwrapper.get_total_results(response_json) is None


def test_get_total_results_response_json_not_dict(unwrapper):
    assert unwrapper.get_total_results("not a dict") is None

def test_get_total_results_float_string(unwrapper):
    response_json = {"header": {"numFound": "100.0"}} # Should fail int conversion
    assert unwrapper.get_total_results(response_json) is None

def test_get_total_results_float_value(unwrapper):
    response_json = {"header": {"numFound": 100.0}}
    assert unwrapper.get_total_results(response_json) == 100

def test_get_total_results_boolean_value(unwrapper):
    # Though not typical, test how it handles other types
    response_json = {"header": {"numFound": True}}
    assert unwrapper.get_total_results(response_json) == 1
    response_json = {"header": {"numFound": False}}
    assert unwrapper.get_total_results(response_json) == 0

def test_get_total_results_object_with_int_conversion(unwrapper):
    class ConvertibleToInt:
        def __int__(self):
            return 50
    response_json = {"header": {"numFound": ConvertibleToInt()}}
    assert unwrapper.get_total_results(response_json) == 50

def test_get_total_results_object_without_int_conversion(unwrapper):
    class NonConvertible:
        pass
    response_json = {"header": {"numFound": NonConvertible()}}
    assert unwrapper.get_total_results(response_json) is None
