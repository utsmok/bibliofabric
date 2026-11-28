"""The unwrapper reads top-level JSON list envelopes."""

from opcitato.unwrapper import OpcitatoUnwrapper

from .conftest import citation


def test_results_reads_the_top_level_list():
    body = [citation(), citation(oci="1-2")]
    assert OpcitatoUnwrapper().results(body) == body


def test_results_drops_non_object_rows():
    assert OpcitatoUnwrapper().results(["nope", citation()]) == [citation()]


def test_results_of_a_non_list_is_empty():
    assert OpcitatoUnwrapper().results({"rows": []}) == []


def test_item_reads_a_single_object():
    row = citation()
    assert OpcitatoUnwrapper().item(row) == row
    assert OpcitatoUnwrapper().item([row]) == {}


def test_total_is_the_list_length_and_next_cursor_is_none():
    unwrapper = OpcitatoUnwrapper()
    assert unwrapper.total([citation()]) == 1
    assert unwrapper.total([]) == 0
    assert unwrapper.total("nope") is None
    assert unwrapper.next_cursor([citation()]) is None


def test_meta_is_always_empty():
    assert OpcitatoUnwrapper().meta([citation()]) == {}
