"""Fake API plumbing shared by the bibliofabric test suite.

Defines a tiny entity model, an unwrapper for a flat ``{"results": [...],
"total": n, "next_cursor": ...}`` envelope, three query dialects (page,
offset, cursor), and concrete resource clients used across test modules.
"""

from typing import Any, ClassVar

import httpx
import pytest
from bibliofabric.client import BaseApiClient
from bibliofabric.config import BaseApiSettings
from bibliofabric.ids import normalize_doi
from bibliofabric.paging import QueryDialect
from bibliofabric.resources import ResourceClient
from pydantic import BaseModel

BASE_URL = "https://fake.test/api"


class Widget(BaseModel):
    id: str = ""
    title: str = ""
    doi: str | None = None


class FakeUnwrapper:
    """Unwraps the fake flat envelope; single-item bodies are the record itself."""

    def results(self, body: Any) -> list[dict[str, Any]]:
        return body.get("results", [])

    def item(self, body: Any) -> dict[str, Any]:
        return body

    def total(self, body: Any) -> int | None:
        return body.get("total")

    def next_cursor(self, body: Any) -> str | None:
        return body.get("next_cursor")

    def meta(self, body: Any) -> dict[str, Any]:
        return {key: value for key, value in body.items() if key != "results"}


PAGE_DIALECT = QueryDialect(
    page_size_param="pageSize",
    max_page_size=100,
    default_page_size=25,
    page_param="page",
    page_start=1,
    sort_param="sort",
    query_param="search",
    select_param="select",
)

OFFSET_DIALECT = QueryDialect(
    page_size_param="rows",
    max_page_size=100,
    page_param=None,
    offset_param="offset",
    page_start=1,
    sort_param="sort",
)

ZERO_START_DIALECT = QueryDialect(
    page_size_param="pageSize",
    max_page_size=100,
    page_param="page",
    page_start=0,
    sort_param="sort",
)

CURSOR_DIALECT = QueryDialect(
    page_size_param="pageSize",
    max_page_size=100,
    page_param=None,
    sort_param="sort",
    query_param="search",
    select_param="select",
    cursor_param="cursor",
    cursor_start="*",
)


class Widgets(ResourceClient[Widget]):
    path = "works"
    model = Widget
    dialect: ClassVar[QueryDialect]


class PageWidgets(Widgets):
    dialect = PAGE_DIALECT


class OffsetWidgets(Widgets):
    dialect = OFFSET_DIALECT


class ZeroStartWidgets(Widgets):
    dialect = ZERO_START_DIALECT


class CursorWidgets(Widgets):
    dialect = CURSOR_DIALECT
    batch_size = 2


class DoiWidgets(CursorWidgets):
    def normalize_id(self, value: str) -> str:
        return normalize_doi(value)


class FakeSettings(BaseApiSettings):
    pass


@pytest.fixture
def make_client(httpx_mock: Any):
    """Build a BaseApiClient whose HTTP traffic goes through pytest-httpx."""

    def _make(**kwargs: Any) -> BaseApiClient:
        http = httpx.AsyncClient(base_url=BASE_URL)
        kwargs.setdefault("settings", FakeSettings())
        return BaseApiClient(
            base_url=BASE_URL,
            unwrapper=FakeUnwrapper(),
            http_client=http,
            **kwargs,
        )

    return _make
