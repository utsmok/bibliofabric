"""The shared Crossref resource-client base; the sync twin is generated."""

from collections.abc import AsyncIterator, Callable, Mapping, Sequence
from typing import Any, ClassVar
from urllib.parse import quote

from bibliofabric import OnError, ResourceClient
from bibliofabric.exceptions import ConfigurationError
from bibliofabric.paging import Page, QueryDialect
from pydantic import BaseModel

from ..dialect import (
    CURSOR_INCOMPATIBLE_SORTS,
    ITERATE_PAGE_SIZE,
    MAX_OFFSET_WINDOW,
    CrossrefDialect,
    _serialize_filters,
    _split_sort,
)


class CrossrefResourceClient[E: BaseModel](ResourceClient[E]):
    """Base for all Crossref resource clients.

    Subclasses declare ``path``, ``model``, and the ``supports_*`` flags
    describing which list parameters the route accepts; the works family
    enables everything, the other routes restrict per the Crossref swagger
    spec (an unsupported parameter is a 400 there, so it is a client-side
    error here).
    """

    dialect: ClassVar[QueryDialect] = CrossrefDialect

    supports_query: ClassVar[bool] = True
    supports_filter: ClassVar[bool] = False
    supports_sort: ClassVar[bool] = False
    supports_select: ClassVar[bool] = False

    # --- hooks ---------------------------------------------------------

    def build_filter_params(
        self, filters: BaseModel | Mapping[str, Any] | None
    ) -> dict[str, str]:
        """Serialize filter criteria into the single ``filter`` parameter."""
        if filters is None:
            return {}
        if isinstance(filters, BaseModel):
            dumped = filters.model_dump(exclude_none=True, by_alias=True)
        else:
            dumped = dict(filters)
        serialized = _serialize_filters(dumped)
        return {"filter": serialized} if serialized else {}

    def format_sort(self, sort: str | Sequence[str]) -> dict[str, str]:
        """Split ``"field:desc"`` into ``sort=<field>`` plus ``order=<desc>``."""
        if self.dialect.sort_param is None:
            return {}
        field, order = _split_sort(sort)
        params: dict[str, str] = {self.dialect.sort_param: field}
        if order is not None:
            params["order"] = order
        return params

    def build_batch_params(self, field: str, values: Sequence[str]) -> dict[str, Any]:
        """Encode one batch chunk as ORed repeated filter keys."""
        return {"filter": _serialize_filters({field: list(values)})}

    def normalize_id(self, value: str | int) -> str:
        """Canonicalize an identifier; member and type ids may be ints."""
        return str(value).strip()

    def item_path(self, id: str) -> str:
        """Return the single-entity path; the slash inside DOIs stays raw."""
        return f"{self.path}/{quote(self.normalize_id(id), safe='/')}"

    # --- operations ----------------------------------------------------

    def iterate(
        self,
        filters: BaseModel | Mapping[str, Any] | None = None,
        *,
        query: str | None = None,
        sort: str | Sequence[str] | None = None,
        select: Sequence[str] | None = None,
        page_size: int | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        on_error: OnError = "raise",
        failures: list[tuple[dict[str, Any], Exception]] | None = None,
        on_page: Callable[[int, str | None], Any] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> AsyncIterator[E]:
        """Iterate all matching entities via Crossref cursor paging.

        Defaults to 1000 rows per page. Rejects the publication-date sorts
        the API no longer allows together with cursors (they fail mid-harvest
        with a 400); sort with a citation field or iterate unsorted.
        """
        if sort is not None:
            field, _ = _split_sort(sort)
            if field in CURSOR_INCOMPATIBLE_SORTS:
                raise ConfigurationError(
                    f"Cursor iteration cannot be combined with sort={field!r}: "
                    "the Crossref API rejects cursor requests sorted by "
                    f"{sorted(CURSOR_INCOMPATIBLE_SORTS)}. Iterate unsorted, or "
                    "sort by a cursor-compatible field such as "
                    "'is-referenced-by-count'."
                )
        return super().iterate(
            filters,
            query=query,
            sort=sort,
            select=select,
            page_size=ITERATE_PAGE_SIZE if page_size is None else page_size,
            limit=limit,
            cursor=cursor,
            on_error=on_error,
            failures=failures,
            on_page=on_page,
            params=params,
        )

    # --- internals -----------------------------------------------------

    def _search_params(
        self,
        *,
        filters: BaseModel | Mapping[str, Any] | None,
        query: str | None = None,
        sort: str | Sequence[str] | None = None,
        select: Sequence[str] | None = None,
        page: int | None = None,
        page_size: int | None = None,
        cursor: str | None = None,
        params: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        self._check_route_params(filters=filters, query=query, sort=sort, select=select)
        query_params = super()._search_params(
            filters=filters,
            query=query,
            sort=sort,
            select=select,
            page=page,
            page_size=page_size,
            cursor=cursor,
            params=params,
        )
        if (
            cursor is None
            and page is not None
            and self.dialect.offset_param is not None
        ):
            size = min(
                page_size if page_size is not None else self.dialect.default_page_size,
                self.dialect.max_page_size,
            )
            offset = (page - self.dialect.page_start) * size
            if offset + size > MAX_OFFSET_WINDOW:
                raise ConfigurationError(
                    f"The Crossref API caps offset paging at offset + rows <= "
                    f"{MAX_OFFSET_WINDOW} (requested offset {offset} + rows "
                    f"{size}); use iterate() for deep result sets."
                )
        return query_params

    def _check_route_params(
        self,
        *,
        filters: BaseModel | Mapping[str, Any] | None,
        query: str | None,
        sort: str | Sequence[str] | None,
        select: Sequence[str] | None,
    ) -> None:
        """Reject parameters the route does not accept (they would 400)."""
        route = f"/{self.path}"
        if sort is not None and not self.supports_sort:
            raise ConfigurationError(
                f"The Crossref {route} route does not support sort."
            )
        if select and not self.supports_select:
            raise ConfigurationError(
                f"The Crossref {route} route does not support select."
            )
        if query and not self.supports_query:
            raise ConfigurationError(
                f"The Crossref {route} route does not support query."
            )
        if filters is not None and not self.supports_filter:
            raise ConfigurationError(
                f"The Crossref {route} route does not support filter."
            )

    async def _request_page(
        self, query_params: dict[str, Any], page: int | None
    ) -> Page[E]:
        """Fetch one list page and wrap it in a :class:`~bibliofabric.paging.Page`."""
        response = await self._client.request("GET", self.path, params=query_params)
        body = response.json()
        unwrapper = self._client.unwrapper
        results = [
            self._validate(record, request=response.request, response=response)
            for record in unwrapper.results(body)
        ]
        return Page(
            results=results,
            total=unwrapper.total(body),
            next_cursor=unwrapper.next_cursor(body),
            page=page,
            meta=unwrapper.meta(body),
        )

    @staticmethod
    def _facet_param(facets: Sequence[str], count: int | None) -> str:
        """Serialize facet requests as ``name:*`` or ``name:<count>`` entries."""
        limit = str(count) if count is not None else "*"
        return ",".join(f"{name}:{limit}" for name in facets)
