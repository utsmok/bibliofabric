"""Funders resource: ``/funders`` and the ``/funders/{id}/works`` scope."""

from collections.abc import AsyncIterator, Mapping, Sequence
from typing import Any
from urllib.parse import quote

from bibliofabric import BaseApiClient, OnError
from bibliofabric.exceptions import ConfigurationError
from bibliofabric.ids import normalize_doi
from bibliofabric.paging import Page
from pydantic import BaseModel

from ..filters import FunderFilters
from ..models import Funder, Work
from .dialect import CrossrefResourceClient
from .works import ScopedWorksResource


class FundersResource(CrossrefResourceClient[Funder]):
    """Typed client for the Crossref ``/funders`` routes.

    Accepts plain ``query`` plus the ``location`` filter.
    """

    path = "funders"
    model = Funder
    filters_model = FunderFilters
    supports_filter = True

    def normalize_id(self, value: str | int) -> str:
        """Return the bare lowercase funder DOI."""
        return normalize_doi(str(value))

    async def descendants(self, funder_id: str) -> list[str]:
        """Return the funder's descendant registry ids from its record.

        Funder ids come back in Crossref's bare form (``"100000025"``).
        Returns an empty list for funders without a hierarchy; list items
        from ``search()`` carry no hierarchy data at all.
        """
        record = await self.get(funder_id)
        return list(record.descendants)

    def works(
        self, funder_id: str, *, include_descendants: bool = False
    ) -> ScopedWorksResource:
        """Return a works client bound to ``funders/{id}/works``.

        ``funder_id`` is the funder's Funder Registry DOI. The scoped route
        already includes descendants' works; with ``include_descendants=True``
        the funder's own id plus its descendant ids are additionally ORed
        into every request's ``funder`` filter, pinning the result set to
        the listed ids.
        """
        funder_id = normalize_doi(funder_id)
        path = f"funders/{quote(funder_id, safe='')}/works"
        if include_descendants:
            return FunderWorksResource(
                self._client, path=path, funders=self, funder_id=funder_id
            )
        return ScopedWorksResource(self._client, path=path)


class FunderWorksResource(ScopedWorksResource):
    """Works client that ORs a funder id plus its descendants into the
    ``funder`` filter of every request.

    The id set is fetched from the funder record on first use and cached.
    Requests that carry their own ``funder`` filter are rejected, since the
    two would silently AND together.
    """

    def __init__(
        self,
        client: BaseApiClient,
        *,
        path: str,
        funders: FundersResource,
        funder_id: str,
    ) -> None:
        super().__init__(client, path=path)
        self._funders = funders
        self._funder_id = funder_id
        self._ids: list[str] | None = None

    async def _funder_ids(self) -> list[str]:
        """The funder id plus its descendants, fetched once."""
        if self._ids is None:
            record = await self._funders.get(self._funder_id)
            self._ids = [self._funder_id, *record.descendants]
        return self._ids

    def build_filter_params(
        self, filters: BaseModel | Mapping[str, Any] | None
    ) -> dict[str, str]:
        if self._ids is None:
            return super().build_filter_params(filters)
        if isinstance(filters, BaseModel):
            merged = filters.model_dump(exclude_none=True, by_alias=True)
        elif filters is None:
            merged = {}
        else:
            merged = dict(filters)
        if "funder" in merged:
            raise ConfigurationError(
                "Pass filters['funder'] or include_descendants=True, not both."
            )
        merged["funder"] = self._ids
        return super().build_filter_params(merged)

    async def search(
        self,
        filters: BaseModel | Mapping[str, Any] | None = None,
        *,
        query: str | None = None,
        sort: str | Sequence[str] | None = None,
        select: Sequence[str] | None = None,
        page: int | None = None,
        page_size: int | None = None,
        cursor: str | None = None,
        on_error: OnError = "raise",
        failures: list[tuple[dict[str, Any], Exception]] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Page[Work]:
        await self._funder_ids()
        return await super().search(
            filters,
            query=query,
            sort=sort,
            select=select,
            page=page,
            page_size=page_size,
            cursor=cursor,
            on_error=on_error,
            failures=failures,
            params=params,
        )

    async def count(
        self,
        filters: BaseModel | Mapping[str, Any] | None = None,
        *,
        query: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> int:
        await self._funder_ids()
        return await super().count(filters, query=query, params=params)

    async def facets(
        self,
        filters: BaseModel | Mapping[str, Any] | None = None,
        *,
        query: str | None = None,
        facets: Sequence[str] = ("*",),
        count: int | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> dict[str, dict[str, int]]:
        await self._funder_ids()
        return await super().facets(
            filters, query=query, facets=facets, count=count, params=params
        )

    async def sample(
        self,
        n: int = 100,
        filters: BaseModel | Mapping[str, Any] | None = None,
        *,
        query: str | None = None,
        select: Sequence[str] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Page[Work]:
        await self._funder_ids()
        return await super().sample(
            n, filters, query=query, select=select, params=params
        )

    def iterate(
        self,
        filters: BaseModel | Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[Work]:
        return self._iterate(filters, **kwargs)

    async def _iterate(
        self,
        filters: BaseModel | Mapping[str, Any] | None,
        **kwargs: Any,
    ) -> AsyncIterator[Work]:
        await self._funder_ids()
        async for entity in super().iterate(filters, **kwargs):  # noqa: UP028
            # the sync twin cannot use ``yield from`` from an async generator
            yield entity
