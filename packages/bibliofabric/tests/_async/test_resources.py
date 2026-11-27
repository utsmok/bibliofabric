"""Query building, iteration, count, and batch_get across the three dialects."""

from collections.abc import Sequence
from typing import Any, cast

import httpx
import pytest
from bibliofabric import ResourceClient
from bibliofabric.exceptions import ConfigurationError, ValidationError
from bibliofabric.paging import Page, QueryDialect
from pydantic import BaseModel

from .conftest import (
    BASE_URL,
    CursorWidgets,
    DoiWidgets,
    FakeSettings,
    OffsetWidgets,
    PageWidgets,
    Widget,
    Widgets,
    ZeroStartWidgets,
)


class TagFilters(BaseModel):
    tag: str
    active: bool | None = None


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
    url = f"{BASE_URL}/works?tag=x&active=true&pageSize=5&page=1&search=foo&select=id,title&sort=title&extra=1"
    httpx_mock.add_response(
        url=url, json=_json_page([{"id": "w1", "title": "T"}], total=1)
    )

    client = make_client()
    works = PageWidgets(client)
    page = await works.search(
        TagFilters(tag="x", active=True),
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
    assert page.page == 1
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


async def test_search_dict_filters_skip_none_and_format_bools(httpx_mock, make_client):
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?tag=x&active=false&pageSize=25&page=1",
        json=_json_page([], total=0),
    )
    client = make_client()
    page = await PageWidgets(client).search(
        {"tag": "x", "empty": None, "active": False}
    )
    assert page.results == []


async def test_search_rejects_positional_search_text(httpx_mock, make_client):
    client = make_client()
    with pytest.raises(ConfigurationError, match="query='water'"):
        await PageWidgets(client).search(cast(Any, "water"))
    assert httpx_mock.get_requests() == []


async def test_search_on_error_skip_and_raise(httpx_mock, make_client):
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?pageSize=25&page=1",
        json=_json_page([{"id": "w1"}, {"title": 123}], total=2),
    )
    client = make_client()
    failures: list[tuple[dict[str, Any], Exception]] = []
    page = await PageWidgets(client).search(on_error="skip", failures=failures)
    assert [widget.id for widget in page.results] == ["w1"]
    assert len(failures) == 1
    assert failures[0][0] == {"title": 123}

    with pytest.raises(ConfigurationError, match="on_error"):
        await PageWidgets(client).search(on_error=cast(Any, "ignore"))


async def test_get_supports_int_id_select_params_and_rejects_empty(
    httpx_mock, make_client
):
    httpx_mock.add_response(
        url=f"{BASE_URL}/works/42?select=id,title&extra=1",
        json={"id": "42", "title": "Answer"},
    )
    client = make_client()
    works = PageWidgets(client)
    widget = await works.get(42, select=["id", "title"], params={"extra": 1})
    assert widget.id == "42"
    with pytest.raises(ConfigurationError, match="non-empty"):
        await works.get("   ")


async def test_exists_head_200_and_404(httpx_mock, make_client):
    httpx_mock.add_response(url=f"{BASE_URL}/works/42", method="HEAD", status_code=200)
    httpx_mock.add_response(url=f"{BASE_URL}/works/99", method="HEAD", status_code=404)
    client = make_client(settings=FakeSettings(max_retries=0))
    works = PageWidgets(client)
    assert await works.exists(42) is True
    assert await works.exists("99") is False


async def test_per_instance_path_override(httpx_mock, make_client):
    httpx_mock.add_response(
        url=f"{BASE_URL}/members/297/works/w1", json={"id": "w1", "title": "Scoped"}
    )
    client = make_client()
    scoped = PageWidgets(client, path="members/297/works")
    widget = await scoped.get("w1")
    assert widget.title == "Scoped"


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


async def test_iterate_cursor_with_none_start_omits_initial_cursor(
    httpx_mock, make_client
):
    token_dialect = QueryDialect(
        page_size_param="limit",
        max_page_size=100,
        default_page_size=10,
        iterate_page_size=2,
        page_param=None,
        cursor_param="token",
        cursor_start=None,
    )

    class TokenWidgets(Widgets):
        dialect = token_dialect

    httpx_mock.add_response(
        url=f"{BASE_URL}/works?limit=2",
        json=_json_page([{"id": "w1"}, {"id": "w2"}], next_cursor="tok2"),
    )
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?limit=2&token=tok2",
        json=_json_page([{"id": "w3"}]),
    )
    client = make_client()
    collected = await TokenWidgets(client).collect()
    assert [widget.id for widget in collected] == ["w1", "w2", "w3"]


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


async def test_iterate_cursor_stops_when_api_echoes_cursor(httpx_mock, make_client):
    # Solr-backed APIs return the request cursor unchanged once results run out.
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?pageSize=2&cursor=c2",
        json=_json_page([{"id": "w3"}], total=3, next_cursor="c2"),
    )
    client = make_client()
    checkpoints: list[tuple[int, str | None]] = []
    collected = [
        widget
        async for widget in CursorWidgets(client).iterate(
            page_size=2, cursor="c2", on_page=lambda n, c: checkpoints.append((n, c))
        )
    ]
    assert [widget.id for widget in collected] == ["w3"]
    assert checkpoints == [(1, None)]


async def test_iterate_cursor_limit_and_zero_limit(httpx_mock, make_client):
    client = make_client()
    assert await CursorWidgets(client).collect(limit=0) == []
    assert await PageWidgets(client).collect(limit=0) == []
    assert httpx_mock.get_requests() == []
    with pytest.raises(ConfigurationError, match="non-negative"):
        CursorWidgets(client).iterate(limit=-1)

    httpx_mock.add_response(
        url=f"{BASE_URL}/works?pageSize=2&cursor=*",
        json=_json_page([{"id": "w1"}, {"id": "w2"}], total=3, next_cursor="c2"),
    )
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
    assert excinfo.value.request is not None
    assert excinfo.value.response is not None


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


async def test_iterate_pages_on_error_skip_stops_at_total(httpx_mock, make_client):
    # total=2 and page 1 returns 2 records (1 invalid skipped): must stop
    # without issuing an extra page 2 request.
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?pageSize=2&page=1",
        json=_json_page([{"id": "w1"}, {"title": 123}], total=2),
    )
    client = make_client()
    failures: list[tuple[dict[str, Any], Exception]] = []
    collected = await PageWidgets(client).collect(
        page_size=2, on_error="skip", failures=failures
    )
    assert [widget.id for widget in collected] == ["w1"]
    assert len(failures) == 1
    assert len(httpx_mock.get_requests()) == 1


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


async def test_iterate_pages_limit_fires_on_page(httpx_mock, make_client):
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?pageSize=2&page=1",
        json=_json_page([{"id": "w1"}, {"id": "w2"}]),
    )
    client = make_client()
    checkpoints: list[tuple[int, str | None]] = []
    collected = [
        widget
        async for widget in PageWidgets(client).iterate(
            page_size=2, limit=1, on_page=lambda n, c: checkpoints.append((n, c))
        )
    ]
    assert [widget.id for widget in collected] == ["w1"]
    assert checkpoints == [(1, None)]
    assert len(httpx_mock.get_requests()) == 1


async def test_count(httpx_mock, make_client):
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?pageSize=1&page=1", json=_json_page([], total=42)
    )
    client = make_client()
    assert await PageWidgets(client).count() == 42


async def test_count_cursor_only_vs_hybrid_and_count_page_size(httpx_mock, make_client):
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?pageSize=1&cursor=*", json=_json_page([], total=7)
    )
    client = make_client()
    assert await CursorWidgets(client).count() == 7

    hybrid_dialect = QueryDialect(
        page_size_param="rows",
        max_page_size=100,
        count_page_size=0,
        page_param=None,
        offset_param="offset",
        cursor_param="cursor",
    )

    class HybridWidgets(Widgets):
        dialect = hybrid_dialect

    httpx_mock.add_response(
        url=f"{BASE_URL}/works?rows=0&offset=0", json=_json_page([], total=99)
    )
    assert await HybridWidgets(client).count() == 99


async def test_batch_get_chunking_and_concurrency(httpx_mock, make_client):
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?id=w1&id=w2&pageSize=2&select=id",
        json=_json_page([{"id": "w1"}, {"id": "w2"}]),
    )
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?id=w3&pageSize=1&select=id",
        json=_json_page([{"id": "w3"}]),
    )
    client = make_client()
    result = await CursorWidgets(client).batch_get(["w1", "w2", "w3"], select=["id"])
    assert set(result) == {"w1", "w2", "w3"}
    assert result["w1"].id == "w1"
    assert len(httpx_mock.get_requests()) == 2


async def test_batch_get_empty_on_error_skip_and_caps_chunk_size(
    httpx_mock, make_client
):
    client = make_client()
    assert await CursorWidgets(client).batch_get([]) == {}
    assert httpx_mock.get_requests() == []

    with pytest.raises(ConfigurationError, match="concurrency"):
        await CursorWidgets(client).batch_get(["w1"], concurrency=0)
    with pytest.raises(ConfigurationError, match="batch_size"):
        await CursorWidgets(client).batch_get(["w1"], batch_size=-1)

    httpx_mock.add_response(
        url=f"{BASE_URL}/works?id=w1&id=w2&pageSize=2",
        json=_json_page([{"id": "w1"}, {"title": 123}]),
    )
    failures: list[tuple[dict[str, Any], Exception]] = []
    result = await CursorWidgets(client).batch_get(
        ["w1", "w2"], on_error="skip", failures=failures
    )
    assert set(result) == {"w1"}
    assert len(failures) == 1
    assert failures[0][0] == {"title": 123}

    # Chunk size is capped at dialect.max_page_size so no results are dropped.
    small_dialect = QueryDialect(
        page_size_param="pageSize",
        max_page_size=2,
        default_page_size=2,
    )

    class SmallPageWidgets(Widgets):
        dialect = small_dialect
        batch_size = 10

    httpx_mock.add_response(
        url=f"{BASE_URL}/works?id=a&id=b&pageSize=2",
        json=_json_page([{"id": "a"}, {"id": "b"}]),
    )
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?id=c&pageSize=1",
        json=_json_page([{"id": "c"}]),
    )
    capped = await SmallPageWidgets(client).batch_get(["a", "b", "c"], batch_size=5)
    assert set(capped) == {"a", "b", "c"}


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


async def test_batch_get_keys_multi_valued_records_by_requested_id(
    httpx_mock, make_client
):
    # Deduplicated records carry several DOIs; the result must use the one asked for.
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?doi=10.1/b&pageSize=1",
        json=_json_page([{"id": "w1", "doi": "10.1/a"}]),
    )

    class MultiDoiWidgets(DoiWidgets):
        def record_keys(self, entity: Widget, field: str) -> list[str]:
            return [self.normalize_id(doi) for doi in ("10.1/a", "10.1/B")]

    client = make_client()
    result = await MultiDoiWidgets(client).batch_get(["10.1/b"], field="doi")
    assert set(result) == {"10.1/b"}


async def test_batch_get_disabled(httpx_mock, make_client):
    client = make_client()

    class Disabled(PageWidgets):
        batch_size = 0

    with pytest.raises(ConfigurationError):
        await Disabled(client).batch_get(["w1"])


async def test_first_defaults_page_size_one_and_empty_returns_none(
    httpx_mock, make_client
):
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?pageSize=1&page=1", json=_json_page([{"id": "w1"}])
    )
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?pageSize=1&page=1", json=_json_page([])
    )
    client = make_client()
    widget = await PageWidgets(client).first()
    assert widget is not None
    assert widget.id == "w1"
    assert await PageWidgets(client).first() is None


async def test_validation_error_carries_raw_payload_and_request(
    httpx_mock, make_client
):
    httpx_mock.add_response(url=f"{BASE_URL}/works/bad", json={"title": 123})
    client = make_client()
    with pytest.raises(ValidationError) as excinfo:
        await PageWidgets(client).get("bad")
    assert excinfo.value.raw == {"title": 123}
    assert excinfo.value.model_name == "Widget"
    assert excinfo.value.request is not None
    assert excinfo.value.response is not None


async def test_fail_fast_unsupported_search_kwargs(httpx_mock, make_client):
    minimal_dialect = QueryDialect(
        page_size_param=None,
        page_param=None,
        offset_param=None,
        cursor_param=None,
        sort_param=None,
        query_param=None,
        select_param=None,
    )

    class MinimalWidgets(Widgets):
        dialect = minimal_dialect

    client = make_client()
    works = MinimalWidgets(client)

    with pytest.raises(ConfigurationError, match="query_param"):
        await works.search(query="hello")
    with pytest.raises(ConfigurationError, match="select_param"):
        await works.search(select=["id"])
    with pytest.raises(ConfigurationError, match="sort_param"):
        await works.search(sort="title")
    with pytest.raises(ConfigurationError, match="cursor_param"):
        await works.search(cursor="*")
    with pytest.raises(ConfigurationError, match="page_param"):
        await works.search(page=2)
    with pytest.raises(ConfigurationError, match="select_param"):
        await works.get("w1", select=["id"])
    with pytest.raises(ConfigurationError, match="select_param"):
        await works.batch_get(["w1"], select=["id"])
    with pytest.raises(ConfigurationError, match="cursor_param"):
        works.iterate(cursor="abc")
    assert httpx_mock.get_requests() == []


async def test_unpaged_dialect_skips_page_size_and_iterates_once(
    httpx_mock, make_client
):
    unpaged_dialect = QueryDialect(
        page_size_param=None,
        page_param=None,
        offset_param=None,
        cursor_param=None,
        sort_param=None,
    )
    client = make_client()
    # Also verifies per-instance dialect override does not mutate class dialect.
    original_dialect = PageWidgets.dialect
    works = PageWidgets(client, dialect=unpaged_dialect)
    assert works.dialect is unpaged_dialect
    assert PageWidgets.dialect is original_dialect

    httpx_mock.add_response(
        url=f"{BASE_URL}/works",
        json=_json_page([{"id": "w1"}, {"id": "w2"}]),
    )
    page = await works.search()
    assert [w.id for w in page.results] == ["w1", "w2"]
    assert page.page is None

    httpx_mock.add_response(
        url=f"{BASE_URL}/works",
        json=_json_page([{"id": "w1"}, {"id": "w2"}]),
    )
    collected = await works.collect()
    assert [w.id for w in collected] == ["w1", "w2"]
    assert len(httpx_mock.get_requests()) == 2

    httpx_mock.add_response(
        url=f"{BASE_URL}/works?id=w1",
        json=_json_page([{"id": "w1"}]),
    )
    batched = await works.batch_get(["w1"])
    assert set(batched) == {"w1"}


async def test_max_offset_enforced_for_page_and_offset_but_not_cursor(
    httpx_mock, make_client
):
    capped_page = QueryDialect(
        page_size_param="per_page",
        max_page_size=100,
        default_page_size=10,
        page_param="page",
        page_start=1,
        max_offset=20,
        cursor_param="cursor",
    )
    capped_offset = QueryDialect(
        page_size_param="rows",
        max_page_size=100,
        default_page_size=10,
        page_param=None,
        offset_param="offset",
        page_start=1,
        max_offset=20,
    )
    client = make_client()
    page_works = PageWidgets(client, dialect=capped_page)
    offset_works = OffsetWidgets(client, dialect=capped_offset)

    # page=3 with size=10 -> offset=20 (allowed); page=4 -> offset=30 (rejected).
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?per_page=10&page=3", json=_json_page([])
    )
    await page_works.search(page=3, page_size=10)
    with pytest.raises(ConfigurationError, match="max_offset"):
        await page_works.search(page=4, page_size=10)

    # Cursor paging bypasses max_offset.
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?per_page=10&cursor=c99", json=_json_page([])
    )
    await page_works.search(cursor="c99", page_size=10)

    # Offset dialect enforcement.
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?rows=10&offset=20", json=_json_page([])
    )
    await offset_works.search(page=3, page_size=10)
    with pytest.raises(ConfigurationError, match="max_offset"):
        await offset_works.search(page=4, page_size=10)


async def test_fetch_batch_chunk_override_for_post_batch(httpx_mock, make_client):
    class PostBatchWidgets(CursorWidgets):
        async def _fetch_batch_chunk(
            self,
            field: str,
            chunk: list[str],
            *,
            select: Sequence[str] | None = None,
        ) -> tuple[list[dict[str, Any]], httpx.Response]:
            params = {"fields": ",".join(select)} if select else None
            response = await self._client.request(
                "POST",
                f"{self.path}/batch",
                params=params,
                json={"ids": chunk},
                retry=True,
            )
            records = self._client.unwrapper.results(self._client.parse_json(response))
            return records, response

    httpx_mock.add_response(
        url=f"{BASE_URL}/works/batch?fields=id,title",
        method="POST",
        match_json={"ids": ["w1", "w2"]},
        json=_json_page([{"id": "w1", "title": "A"}, {"title": 123}]),
    )
    httpx_mock.add_response(
        url=f"{BASE_URL}/works/batch?fields=id,title",
        method="POST",
        match_json={"ids": ["w3"]},
        json=_json_page([{"id": "w3", "title": "C"}]),
    )
    client = make_client()
    failures: list[tuple[dict[str, Any], Exception]] = []
    result = await PostBatchWidgets(client).batch_get(
        [" w1 ", "w2", "w1", "w3"],
        select=["id", "title"],
        on_error="skip",
        failures=failures,
    )
    assert set(result) == {"w1", "w3"}
    assert len(failures) == 1
    assert failures[0][0] == {"title": 123}
    assert len(httpx_mock.get_requests(method="POST")) == 2


async def test_bulk_list_adapter_cached_per_subclass_and_preserves_raw_error(
    httpx_mock, make_client
):
    class OtherWidget(BaseModel):
        code: int

    class OtherWidgets(ResourceClient[OtherWidget]):
        path = "others"
        model = OtherWidget
        dialect = PageWidgets.dialect

    client = make_client()
    page_works = PageWidgets(client)
    other_works = OtherWidgets(client)

    httpx_mock.add_response(
        url=f"{BASE_URL}/works?pageSize=25&page=1",
        json=_json_page([{"id": "w1"}, {"id": "w2"}]),
    )
    page = await page_works.search()
    assert [w.id for w in page.results] == ["w1", "w2"]
    first_adapter = PageWidgets._list_adapter
    assert first_adapter is not None

    # Second call reuses the cached adapter.
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?pageSize=25&page=1",
        json=_json_page([{"id": "w3"}]),
    )
    await page_works.search()
    assert PageWidgets._list_adapter is first_adapter

    # Subclass with a different model gets its own adapter.
    httpx_mock.add_response(
        url=f"{BASE_URL}/others?pageSize=25&page=1",
        json=_json_page([{"code": 7}]),
    )
    other_page = await other_works.search()
    assert [o.code for o in other_page.results] == [7]
    assert OtherWidgets._list_adapter is not None
    assert OtherWidgets._list_adapter is not first_adapter

    # Validation error in a multi-record page falls back to _validate() and
    # attaches the exact offending record in .raw.
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?pageSize=25&page=1",
        json=_json_page([{"id": "ok"}, {"title": 999}]),
    )
    with pytest.raises(ValidationError) as excinfo:
        await page_works.search()
    assert excinfo.value.raw == {"title": 999}
    assert excinfo.value.model_name == "Widget"
    assert excinfo.value.request is not None
    assert excinfo.value.response is not None

    # iterate(limit=1) only validates up to the limit, so a trailing bad record
    # beyond limit does not cause a spurious failure.
    httpx_mock.add_response(
        url=f"{BASE_URL}/works?pageSize=2&page=1",
        json=_json_page([{"id": "good"}, {"title": 999}]),
    )
    limited = await page_works.collect(page_size=2, limit=1)
    assert [w.id for w in limited] == ["good"]
