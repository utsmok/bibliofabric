"""JSON:API envelope reading."""

from bibliofabric.unwrap import JsonApiUnwrapper


def test_json_api_unwrapper_reads_records_total_cursor_and_meta():
    unwrapper = JsonApiUnwrapper()
    body = {
        "data": [
            {"id": "10.1234/a", "type": "dois", "attributes": {"doi": "10.1234/a"}},
            "not a record",
        ],
        "meta": {"total": 143, "page": 1},
        "links": {
            "self": "https://api.test/dois?page[cursor]=1&page[size]=25",
            "next": "https://api.test/dois?page[cursor]=25&page[size]=25",
        },
        "included": [],
    }
    assert [record["id"] for record in unwrapper.results(body)] == ["10.1234/a"]
    assert unwrapper.total(body) == 143
    assert unwrapper.next_cursor(body) == "25"
    assert unwrapper.meta(body) == {
        "meta": {"total": 143, "page": 1},
        "links": body["links"],
        "included": [],
    }


def test_json_api_unwrapper_cursor_comes_from_links_next_only():
    unwrapper = JsonApiUnwrapper()
    relative = {"links": {"next": "/dois?page%5Bcursor%5D=abc&page%5Bsize%5D=25"}}
    assert unwrapper.next_cursor(relative) == "abc"
    assert unwrapper.next_cursor({"links": {"next": "/dois?page[size]=25"}}) is None
    assert unwrapper.next_cursor({"links": {"next": None}}) is None
    assert unwrapper.next_cursor({"data": []}) is None
    assert (
        JsonApiUnwrapper("cursor").next_cursor({"links": {"next": "/items?cursor=z9"}})
        == "z9"
    )


def test_json_api_unwrapper_single_item_and_malformed_bodies():
    unwrapper = JsonApiUnwrapper()
    item = {"id": "x", "type": "dois", "attributes": {}}
    assert unwrapper.item({"data": item}) == item
    assert unwrapper.item({"data": []}) == {}
    assert unwrapper.item({"errors": [{"status": "404"}]}) == {}
    assert unwrapper.results([]) == []
    assert unwrapper.results({"data": {"id": "x"}}) == []
    assert unwrapper.total({"meta": {"total": "7"}}) is None
    assert unwrapper.total({"meta": {}}) is None
    assert unwrapper.meta(None) == {}
