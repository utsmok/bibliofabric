"""Types resource: ``/types`` and the ``/types/{id}/works`` scope."""

from collections.abc import AsyncIterator, Callable, Mapping, Sequence
from typing import Any
from urllib.parse import quote

from bibliofabric import OnError
from bibliofabric._async._concurrency import maybe_await
from bibliofabric.exceptions import ConfigurationError
from pydantic import BaseModel

from ..models import CrossRefType
from .dialect import CrossrefResourceClient
from .works import ScopedWorksResource

_VALID_ON_ERROR = frozenset({"raise", "skip"})


class TypesResource(CrossrefResourceClient[CrossRefType]):
    """Typed client for the Crossref ``/types`` routes.

    The type list serves no ``query``, ``filter``, ``sort``, or ``select``;
    any of those parameters is rejected client-side. Crossref ignores
    ``rows`` and ``offset`` on ``/types`` and always returns the complete
    list in one response, so ``count()`` and ``iterate()`` issue a single
    unpaged fetch.
    """

    path = "types"
    model = CrossRefType
    supports_query = False

    def works(self, type_id: str | int) -> ScopedWorksResource:
        """Return a works client bound to ``types/{id}/works``."""
        type_id = quote(str(type_id).strip(), safe="")
        return ScopedWorksResource(self._client, path=f"types/{type_id}/works")

    async def count(
        self,
        filters: BaseModel | Mapping[str, Any] | None = None,
        *,
        query: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> int:
        """Return the total number of Crossref work types (single unpaged fetch)."""
        self._check_route_params(filters=filters, query=query, sort=None, select=None)
        response = await self._client.request("GET", self.path, params=params)
        body = self._client.parse_json(response)
        unwrapper = self._client.unwrapper
        total = unwrapper.total(body)
        return total if total is not None else len(unwrapper.results(body))

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
    ) -> AsyncIterator[CrossRefType]:
        """Yield all Crossref work types from a single unpaged fetch."""
        if on_error not in _VALID_ON_ERROR:
            raise ConfigurationError(
                f"on_error must be 'raise' or 'skip', got {on_error!r}."
            )
        if limit is not None and limit < 0:
            raise ConfigurationError(f"limit must be non-negative, got {limit}.")
        if cursor is not None:
            raise ConfigurationError(
                f"The Crossref /{self.path} route does not support cursor paging."
            )
        self._check_route_params(filters=filters, query=query, sort=sort, select=select)
        return self._iterate(
            limit=limit,
            on_error=on_error,
            failures=failures,
            on_page=on_page,
            params=params,
        )

    async def _iterate(
        self,
        *,
        limit: int | None,
        on_error: OnError,
        failures: list[tuple[dict[str, Any], Exception]] | None,
        on_page: Callable[[int, str | None], Any] | None,
        params: Mapping[str, Any] | None,
    ) -> AsyncIterator[CrossRefType]:
        if limit == 0:
            return
        response = await self._client.request("GET", self.path, params=params)
        body = self._client.parse_json(response)
        fetched = 0
        for record in self._client.unwrapper.results(body):
            entity = self._parse_or_handle(
                record,
                on_error=on_error,
                failures=failures,
                request=response.request,
                response=response,
            )
            if entity is None:
                continue
            yield entity
            fetched += 1
            if limit is not None and fetched >= limit:
                break
        if on_page is not None:
            await maybe_await(on_page(1, None))
