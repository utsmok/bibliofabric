"""The ``ZenothecaUnwrapper`` reads the ``hits`` envelope."""

from zenotheca.unwrapper import ZenothecaUnwrapper


def envelope(**extra):
    return {
        "hits": {"hits": [{"id": 1}, {"id": 2}], "total": 97},
        "links": {"self": "https://zenodo.org/api/records"},
        "aggregations": {"access_status": {"buckets": []}},
        **extra,
    }


def test_results_reads_hits_hits():
    assert ZenothecaUnwrapper().results(envelope()) == [{"id": 1}, {"id": 2}]


def test_results_of_shapes_without_hits_is_empty():
    assert ZenothecaUnwrapper().results({"message": "no"}) == []
    assert ZenothecaUnwrapper().results({"hits": {"hits": "no"}}) == []
    assert ZenothecaUnwrapper().results(None) == []


def test_item_returns_the_record_itself():
    body = {"id": 24378467}
    assert ZenothecaUnwrapper().item(body) is body
    assert ZenothecaUnwrapper().item([1]) == {}


def test_total_reads_hits_total():
    assert ZenothecaUnwrapper().total(envelope()) == 97
    assert ZenothecaUnwrapper().total({"hits": {}}) is None
    assert ZenothecaUnwrapper().total({}) is None


def test_next_cursor_is_always_none():
    assert ZenothecaUnwrapper().next_cursor(envelope()) is None


def test_meta_is_the_envelope_minus_hits():
    meta = ZenothecaUnwrapper().meta(envelope(page=1, sortBy="bestmatch"))
    assert meta == {
        "links": {"self": "https://zenodo.org/api/records"},
        "aggregations": {"access_status": {"buckets": []}},
        "page": 1,
        "sortBy": "bestmatch",
    }
    assert ZenothecaUnwrapper().meta("no") == {}
