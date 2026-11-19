"""Query building, iteration, count, and batch_get across the three dialects."""

import pytest
from pydantic import BaseModel

from bibliofabric.exceptions import ConfigurationError, ValidationError
from bibliofabric.paging import Page

from .conftest import (
    BASE_URL,
    CursorWidgets,
    DoiWidgets,
    OffsetWidgets,
    PageWidgets,
    Widget,
    ZeroStartWidgets,
)


class TagFilters(BaseModel):
    tag: str


def _json_page(
    items: list[dict], total: int | None = None, next_cursor: str | None = None
) -> dict:
    body: dict = {"results": items}
    if total is not None:
        body["total"] = total
    if next_cursor is not None:
        body["next_cursor"] = next_cursor
    return body


async def test_search_page_dialect_params(httpx_mock, make_client):
    url = f"{BASE_URL}/works?tag=x&pageSize=5&page=1&search=foo&select=id,title&sort=title&extra=1"
    httpx_mock.add_response(
        url=url, json=_json_page([{"id": "w1", "title": "T"}], total=1)
    )

    client = make_client()
    works = PageWidgets(client)
    page = await works.search(
        TagFilters(tag="x"),
        query="foo",
        sort="title",
        select=["id", "title"],
        page_size=5,
        params={"extra": 1},
    )
    assert isinstance(page, Page)
    assert page.results == [Widget(id="w1", title="T")]
    assert page.total == 1
    assert page.next_cursor is None
    assert page.meta == {"total": 1}


async def test_search_offset_dialect_params(httpx_mock, make_client):
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?rows=3&offset=3", json=_json_page([], total=0)
    )
    client = make_client()
    works = OffsetWidgets(client)
    page = await works.search(page=2, page_size=3)
    assert page.page == 2


async def test_search_cursor_dialect_params(httpx_mock, make_client):
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?pageSize=5&cursor=abc", json=_json_page([], total=0)
    )
    client = make_client()
    works = CursorWidgets(client)
    page = await works.search(cursor="abc", page_size=5)
    assert page.page is None


async def test_search_dict_filters(httpx_mock, make_client):
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?tag=x&pageSize=25&page=1", json=_json_page([], total=0)
    )
    client = make_client()
    page = await PageWidgets(client).search({"tag": "x"})
    assert page.results == []


async def test_iterate_cursor_two_pages(httpx_mock, make_client):
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?pageSize=2&cursor=*",
        json=_json_page([{"id": "w1"}, {"id": "w2"}], total=3, next_cursor="c2"),
    )
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?pageSize=2&cursor=c2",
        json=_json_page([{"id": "w3"}], total=3),
    )
    client = make_client()
    checkpoints: list[tuple[int, str | None]] = []
    collected = [
        widget
        async for widget in CursorWidgets(client).iterate(
            page_size=2, on_page=lambda n, c: checkpoints.append((n, c))
        )
    ]
    assert [widget.id for widget in collected] == ["w1", "w2", "w3"]
    assert checkpoints == [(1, "c2"), (2, None)]


async def test_iterate_cursor_resume(httpx_mock, make_client):
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?pageSize=2&cursor=c2",
        json=_json_page([{"id": "w3"}], total=3),
    )
    client = make_client()
    collected = [
        widget
        async for widget in CursorWidgets(client).iterate(page_size=2, cursor="c2")
    ]
    assert [widget.id for widget in collected] == ["w3"]


async def test_iterate_cursor_limit(httpx_mock, make_client):
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?pageSize=2&cursor=*",
        json=_json_page([{"id": "w1"}, {"id": "w2"}], total=3, next_cursor="c2"),
    )
    client = make_client()
    checkpoints: list[tuple[int, str | None]] = []
    collected = [
        widget
        async for widget in CursorWidgets(client).iterate(
            page_size=2, limit=1, on_page=lambda n, c: checkpoints.append((n, c))
        )
    ]
    assert [widget.id for widget in collected] == ["w1"]
    assert checkpoints == [(1, "c2")]


async def test_iterate_cursor_on_error_skip_and_raise(httpx_mock, make_client):
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?pageSize=2&cursor=*",
        json=_json_page([{"id": "w1"}, {"title": 123}], total=1),
    )
    client = make_client()
    failures: list[tuple[dict, Exception]] = []
    collected = [
        widget
        async for widget in CursorWidgets(client).iterate(
            page_size=2, on_error="skip", failures=failures
        )
    ]
    assert [widget.id for widget in collected] == ["w1"]
    assert len(failures) == 1
    assert failures[0][0] == {"title": 123}

    httpx_mock.add_response(
        url=f"{BASE_URL}/works?pageSize=2&cursor=*",
        json=_json_page([{"title": 123}], total=1),
    )
    with pytest.raises(ValidationError) as excinfo:
        _ = [widget async for widget in CursorWidgets(client).iterate(page_size=2)]
    assert excinfo.value.raw == {"title": 123}
    assert excinfo.value.model_name == "Widget"


async def test_iterate_pages_from_one(httpx_mock, make_client):
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?pageSize=2&page=1",
        json=_json_page([{"id": "w1"}, {"id": "w2"}]),
    )
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?pageSize=2&page=2", json=_json_page([])
    )
    client = make_client()
    checkpoints: list[tuple[int, str | None]] = []
    collected = [
        widget
        async for widget in PageWidgets(client).iterate(
            page_size=2, on_page=lambda n, c: checkpoints.append((n, c))
        )
    ]
    assert [widget.id for widget in collected] == ["w1", "w2"]
    assert checkpoints == [(1, None), (2, None)]


async def test_iterate_pages_from_zero(httpx_mock, make_client):
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?pageSize=2&page=0", json=_json_page([{"id": "w1"}])
    )
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?pageSize=2&page=1", json=_json_page([])
    )
    client = make_client()
    collected = [
        widget async for widget in ZeroStartWidgets(client).iterate(page_size=2)
    ]
    assert [widget.id for widget in collected] == ["w1"]


async def test_iterate_offset_stops_at_total(httpx_mock, make_client):
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?rows=2&offset=0",
        json=_json_page([{"id": "w1"}, {"id": "w2"}], total=3),
    )
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?rows=2&offset=2",
        json=_json_page([{"id": "w3"}], total=3),
    )
    client = make_client()
    collected = [widget async for widget in OffsetWidgets(client).iterate(page_size=2)]
    assert [widget.id for widget in collected] == ["w1", "w2", "w3"]


async def test_iterate_pages_limit(httpx_mock, make_client):
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?pageSize=2&page=1",
        json=_json_page([{"id": "w1"}, {"id": "w2"}]),
    )
    client = make_client()
    collected = [
        widget async for widget in PageWidgets(client).iterate(page_size=2, limit=1)
    ]
    assert [widget.id for widget in collected] == ["w1"]
    assert len(httpx_mock.get_requests()) == 1


async def test_count(httpx_mock, make_client):
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?pageSize=1&page=1", json=_json_page([], total=42)
    )
    client = make_client()
    assert await PageWidgets(client).count() == 42


async def test_count_cursor_dialect(httpx_mock, make_client):
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?pageSize=1&cursor=*", json=_json_page([], total=7)
    )
    client = make_client()
    assert await CursorWidgets(client).count() == 7


async def test_batch_get_chunking_and_concurrency(httpx_mock, make_client):
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?id=w1&id=w2&pageSize=2",
        json=_json_page([{"id": "w1"}, {"id": "w2"}]),
    )
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?id=w3&pageSize=1",
        json=_json_page([{"id": "w3"}]),
    )
    client = make_client()
    result = await CursorWidgets(client).batch_get(["w1", "w2", "w3"])
    assert set(result) == {"w1", "w2", "w3"}
    assert result["w1"].id == "w1"
    assert len(httpx_mock.get_requests()) == 2


async def test_batch_get_missing_ids_absent(httpx_mock, make_client):
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?id=w1&id=w2&pageSize=2",
        json=_json_page([{"id": "w1"}]),
    )
    client = make_client()
    result = await CursorWidgets(client).batch_get(["w1", "w2"])
    assert set(result) == {"w1"}


async def test_batch_get_normalizes_keys(httpx_mock, make_client):
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?doi=10.1234/abc&pageSize=1",
        json=_json_page([{"id": "w9", "doi": "10.1234/ABC"}]),
    )
    client = make_client()
    result = await DoiWidgets(client).batch_get(
        ["https://doi.org/10.1234/ABC"], field="doi"
    )
    assert set(result) == {"10.1234/abc"}
    assert result["10.1234/abc"].id == "w9"


async def test_batch_get_disabled(httpx_mock, make_client):
    client = make_client()

    class Disabled(PageWidgets):
        batch_size = 0

    with pytest.raises(ConfigurationError):
        await Disabled(client).batch_get(["w1"])


async def test_first(httpx_mock, make_client):
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?pageSize=1&page=1", json=_json_page([{"id": "w1"}])
    )
    client = make_client()
    widget = await PageWidgets(client).first(page_size=1)
    assert widget is not None
    assert widget.id == "w1"


async def test_validation_error_carries_raw_payload(httpx_mock, make_client):
    httpx_mock.add_response(url=f"{BASE_URL}/works/bad", json={"title": 123})
    client = make_client()
    with pytest.raises(ValidationError) as excinfo:
        await PageWidgets(client).get("bad")
    assert excinfo.value.raw == {"title": 123}
    assert excinfo.value.model_name == "Widget"
