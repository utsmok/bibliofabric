"""Client for Europe PMC preprint searches."""

from collections.abc import AsyncIterator, Callable, Mapping, Sequence
from typing import Any, override

from bibliofabric import OnError
from bibliofabric.paging import Page
from pydantic import BaseModel

from ..models import SearchResult
from .search import ResultType, SearchClient

PPR_SOURCE = "SRC:PPR"


class PreprintsClient(SearchClient):
    """Client for preprint records in Europe PMC.

    Europe PMC indexes preprints under the ``PPR`` source; they surface
    through the same ``/search`` route. The client adds ``SRC:PPR`` to every
    query so callers search the preprint subset only.
    """

    @override
    async def search(
        self,
        filters: BaseModel | Mapping[str, Any] | None = None,
        *,
        query: str | None = None,
        sort: str | Sequence[str] | None = None,
        select: Sequence[str] | None = None,
        result_type: ResultType = "core",
        synonym: bool = False,
        page_size: int | None = None,
        page: int | None = None,
        cursor: str | None = None,
        on_error: OnError = "raise",
        failures: list[tuple[dict[str, Any], Exception]] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Page[SearchResult]:
        """Fetch one page of preprint search results."""
        return await super().search(
            filters,
            query=self._ppr_query(query),
            sort=sort,
            select=select,
            result_type=result_type,
            synonym=synonym,
            page_size=page_size,
            page=page,
            cursor=cursor,
            on_error=on_error,
            failures=failures,
            params=params,
        )

    @override
    def iterate(
        self,
        filters: BaseModel | Mapping[str, Any] | None = None,
        *,
        query: str | None = None,
        sort: str | Sequence[str] | None = None,
        select: Sequence[str] | None = None,
        result_type: ResultType = "core",
        synonym: bool = False,
        page_size: int | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        on_error: OnError = "raise",
        failures: list[tuple[dict[str, Any], Exception]] | None = None,
        on_page: Callable[[int, str | None], Any] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> AsyncIterator[SearchResult]:
        """Iterate over all matching preprints, cursor page by cursor page."""
        return super().iterate(
            filters,
            query=self._ppr_query(query),
            sort=sort,
            select=select,
            result_type=result_type,
            synonym=synonym,
            page_size=page_size,
            limit=limit,
            cursor=cursor,
            on_error=on_error,
            failures=failures,
            on_page=on_page,
            params=params,
        )

    @staticmethod
    def _ppr_query(query: str | None) -> str | None:
        """Constrain a query to the preprint source."""
        if not query:
            return PPR_SOURCE
        if query == PPR_SOURCE or query.startswith(f"{PPR_SOURCE} AND"):
            return query
        return f"{PPR_SOURCE} AND ({query})"


__all__ = ["PPR_SOURCE", "PreprintsClient"]
