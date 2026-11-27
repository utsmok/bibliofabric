"""Works resources: the top-level ``/works`` route and parent-scoped works."""

from collections.abc import AsyncIterator, Callable, Collection, Mapping, Sequence
from datetime import UTC, datetime
from typing import Any, ClassVar

from bibliofabric import BaseApiClient, OnError, validate_model
from bibliofabric.exceptions import ConfigurationError
from bibliofabric.ids import normalize_doi
from bibliofabric.paging import Page, QueryDialect
from pydantic import BaseModel

from ..dialect import CrossrefDialect
from ..filters import WorksFilters
from ..models import Work, WorkAgency
from ..models.base import UpdateTo
from .dialect import CrossrefResourceClient

#: Crossref caps facet value counts at 1000 and ``sample`` at 100.
MAX_FACET_COUNT = 1000
MAX_SAMPLE = 100

#: Default Crossmark ``updated-by`` types followed by ``latest_version()``.
DEFAULT_VERSION_UPDATE_TYPES: tuple[str, ...] = ("new_version", "new_edition")


def _update_timestamp(entry: UpdateTo) -> float:
    """Return a sortable millisecond timestamp for an ``updated-by`` entry."""
    if entry.updated is None:
        return 0.0
    if entry.updated.timestamp is not None:
        return float(entry.updated.timestamp)
    for part in entry.updated.date_parts:
        if part:
            year, month, day = (*part, 1, 1)[:3]
            try:
                return datetime(year, month, day, tzinfo=UTC).timestamp() * 1000
            except ValueError:
                return float(year)
    return 0.0


class _WorksBaseClient(CrossrefResourceClient[Work]):
    """Internal ``ResourceClient`` backing :class:`_WorksListResource`."""

    path = "works"
    model = Work
    dialect = CrossrefDialect
    filters_model = WorksFilters
    supports_filter = True
    batch_size = 50

    def __init__(
        self,
        client: BaseApiClient,
        *,
        path: str | None = None,
        owner: "_WorksListResource | None" = None,
    ) -> None:
        super().__init__(client, path=path)
        self._owner = owner

    def normalize_id(self, value: str | int) -> str:
        """Return the bare lowercase DOI (DOIs are case-insensitive)."""
        return normalize_doi(str(value))

    def build_filter_params(
        self, filters: BaseModel | Mapping[str, Any] | None
    ) -> dict[str, str]:
        if self._owner is not None:
            return self._owner.build_filter_params(filters)
        return super().build_filter_params(filters)


class _WorksListResource:
    """Shared list, search, iterate, count, facets, sample, and batch methods for works."""

    path: str = "works"
    model: ClassVar[type[Work]] = Work
    dialect: ClassVar[QueryDialect] = CrossrefDialect
    filters_model: ClassVar[type[WorksFilters]] = WorksFilters
    supports_filter: ClassVar[bool] = True
    batch_size: ClassVar[int] = 50

    def __init__(self, client: BaseApiClient, *, path: str | None = None) -> None:
        self._client = client
        if path is not None:
            self.path = path
        self._resource = _WorksBaseClient(client, path=self.path, owner=self)

    def normalize_id(self, value: str | int) -> str:
        """Return the bare lowercase DOI (DOIs are case-insensitive)."""
        return normalize_doi(str(value))

    def build_filter_params(
        self, filters: BaseModel | Mapping[str, Any] | None
    ) -> dict[str, str]:
        """Serialize filter criteria into Crossref's single ``filter`` parameter."""
        return CrossrefResourceClient.build_filter_params(self._resource, filters)

    def format_sort(self, sort: str | Sequence[str]) -> dict[str, str]:
        """Split ``"field:desc"`` into ``sort=<field>`` plus ``order=<desc>``."""
        return self._resource.format_sort(sort)

    def build_batch_params(self, field: str, values: Sequence[str]) -> dict[str, Any]:
        """Encode one batch chunk as ORed repeated filter keys."""
        return self._resource.build_batch_params(field, values)

    def record_keys(self, entity: Work, field: str) -> list[str]:
        """Return every normalized ``field`` value of ``entity``."""
        return self._resource.record_keys(entity, field)

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
        """Fetch one page of works; ``params`` carries extras such as
        ``{"query.bibliographic": "...", "sample": 50}`` (works accepts the
        ``query.*`` sub-fields; other routes take plain ``query`` only)."""
        return await self._resource.search(
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
    ) -> AsyncIterator[Work]:
        """Iterate all matching works using Crossref cursor paging."""
        return self._resource.iterate(
            filters,
            query=query,
            sort=sort,
            select=select,
            page_size=page_size,
            limit=limit,
            cursor=cursor,
            on_error=on_error,
            failures=failures,
            on_page=on_page,
            params=params,
        )

    async def collect(
        self,
        filters: BaseModel | Mapping[str, Any] | None = None,
        *,
        limit: int | None = None,
        query: str | None = None,
        sort: str | Sequence[str] | None = None,
        select: Sequence[str] | None = None,
        page_size: int | None = None,
        cursor: str | None = None,
        on_error: OnError = "raise",
        failures: list[tuple[dict[str, Any], Exception]] | None = None,
        on_page: Callable[[int, str | None], Any] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> list[Work]:
        """Collect ``iterate()`` output into a list, optionally bounded."""
        return [
            entity
            async for entity in self.iterate(
                filters,
                query=query,
                sort=sort,
                select=select,
                page_size=page_size,
                limit=limit,
                cursor=cursor,
                on_error=on_error,
                failures=failures,
                on_page=on_page,
                params=params,
            )
        ]

    async def first(
        self,
        filters: BaseModel | Mapping[str, Any] | None = None,
        *,
        query: str | None = None,
        sort: str | Sequence[str] | None = None,
        select: Sequence[str] | None = None,
        page_size: int | None = 1,
        cursor: str | None = None,
        on_error: OnError = "raise",
        failures: list[tuple[dict[str, Any], Exception]] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Work | None:
        """Return the first matching work, or ``None`` when there is none."""
        results = await self.collect(
            filters,
            limit=1,
            query=query,
            sort=sort,
            select=select,
            page_size=page_size,
            cursor=cursor,
            on_error=on_error,
            failures=failures,
            params=params,
        )
        return results[0] if results else None

    async def count(
        self,
        filters: BaseModel | Mapping[str, Any] | None = None,
        *,
        query: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> int:
        """Return the total number of matching works using ``rows=0``."""
        return await self._resource.count(filters, query=query, params=params)

    async def batch_get(
        self,
        ids: Sequence[str],
        *,
        field: str = "id",
        select: Sequence[str] | None = None,
        batch_size: int | None = None,
        concurrency: int = 4,
        on_error: OnError = "raise",
        failures: list[tuple[dict[str, Any], Exception]] | None = None,
    ) -> dict[str, Work]:
        """Fetch works for many ids in bounded, concurrent chunks."""
        return await self._resource.batch_get(
            ids,
            field=field,
            select=select,
            batch_size=batch_size,
            concurrency=concurrency,
            on_error=on_error,
            failures=failures,
        )

    async def batch_get_by_doi(
        self,
        dois: Sequence[str],
        *,
        select: Sequence[str] | None = None,
        batch_size: int | None = None,
        concurrency: int = 4,
        on_error: OnError = "raise",
        failures: list[tuple[dict[str, Any], Exception]] | None = None,
    ) -> dict[str, Work]:
        """Fetch many works by DOI in bounded, concurrent filter batches.

        Uses Crossref's repeated-key OR syntax (``filter=doi:a,doi:b``) with
        up to 50 DOIs per request. Returns a dict keyed by bare lowercase
        DOI; DOIs not found are absent.
        """
        return await self.batch_get(
            dois,
            field="doi",
            select=select,
            batch_size=batch_size,
            concurrency=concurrency,
            on_error=on_error,
            failures=failures,
        )

    async def facets(
        self,
        filters: BaseModel | Mapping[str, Any] | None = None,
        *,
        query: str | None = None,
        facets: Sequence[str] = ("*",),
        count: int | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> dict[str, dict[str, int]]:
        """Return approximate facet counts for a filter set.

        Requests the given facet names (``*`` for all) with ``rows=0``, and
        returns ``{facet_name: {value: count}}``. ``count`` caps the values
        per facet (Crossref allows up to 1000); the API also reports a
        ``value-count`` per facet, which this helper drops.
        """
        if count is not None and not 1 <= count <= MAX_FACET_COUNT:
            raise ConfigurationError(
                f"Facet count must be between 1 and {MAX_FACET_COUNT}, got {count}."
            )
        query_params = self._resource._search_params(
            filters=filters, query=query, page=1, page_size=0, params=params
        )
        query_params["facet"] = self._resource._facet_param(facets, count)
        page = await self._resource._request_page(query_params, page=1)
        raw = page.meta.get("facets") or {}
        return {
            str(name): {
                str(value): int(total)
                for value, total in entry.get("values", {}).items()
                if isinstance(total, int | float)
            }
            for name, entry in raw.items()
            if isinstance(entry, dict)
        }

    async def sample(
        self,
        n: int = 100,
        filters: BaseModel | Mapping[str, Any] | None = None,
        *,
        query: str | None = None,
        select: Sequence[str] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Page[Work]:
        """Fetch up to ``n`` random works (Crossref caps ``sample`` at 100).

        ``sample`` cannot be combined with ``rows`` or ``offset``, so the
        returned page is a random draw, not the head of the result set.
        """
        if not 1 <= n <= MAX_SAMPLE:
            raise ConfigurationError(
                f"The Crossref API caps sample at 100 works, got n={n}."
            )
        query_params = self._resource._search_params(
            filters=filters, query=query, select=select, params=params
        )
        query_params.pop(self.dialect.page_size_param or "", None)
        query_params.pop(self.dialect.offset_param or "", None)
        query_params["sample"] = n
        return await self._resource._request_page(query_params, page=None)


class WorksResource(_WorksListResource):
    """Typed client for the Crossref ``/works`` route."""

    def item_path(self, id: str | int) -> str:
        """Return the single-work path with the DOI percent-encoded."""
        return self._resource.item_path(id)

    async def get(
        self,
        id: str | int,
        *,
        select: Sequence[str] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Work:
        """Fetch one work by DOI; 404 raises :class:`NotFoundError`."""
        return await self._resource.get(id, select=select, params=params)

    async def exists(self, id: str | int) -> bool:
        """Return ``True`` when the DOI exists (HTTP HEAD); 404 returns ``False``."""
        return await self._resource.exists(id)

    async def agency(self, doi: str) -> WorkAgency:
        """Look up the DOI registration agency for a work."""
        response = await self._client.request("GET", f"{self.item_path(doi)}/agency")
        data = self._client.unwrapper.item(self._client.parse_json(response))
        return validate_model(
            WorkAgency, data, request=response.request, response=response
        )

    async def latest_version(
        self,
        doi: str,
        update_types: Collection[str] | None = DEFAULT_VERSION_UPDATE_TYPES,
    ) -> Work:
        """Resolve a DOI to the newest record in its Crossmark update chain.

        Older records of an update chain carry ``updated-by`` entries naming
        the works that updated them, each with a ``type`` and a timestamp or
        date parts. By default only ``("new_version", "new_edition")`` entries
        are followed so retractions and corrections are not mistaken for newer
        versions; pass ``update_types=None`` to follow all Crossmark updates.
        A DOI without matching update data is returned unchanged.
        """
        allowed = set(update_types) if update_types is not None else None
        work = await self.get(doi)
        seen = {self.normalize_id(doi)}
        if work.doi:
            seen.add(self.normalize_id(work.doi))
        while work.updated_by:
            candidates = (
                [entry for entry in work.updated_by if entry.type in allowed]
                if allowed is not None
                else work.updated_by
            )
            if not candidates:
                break
            newest = max(candidates, key=_update_timestamp)
            target = newest.doi
            if not target or self.normalize_id(target) in seen:
                break
            seen.add(self.normalize_id(target))
            work = await self.get(target)
            if work.doi:
                seen.add(self.normalize_id(work.doi))
        return work


class ScopedWorksResource(_WorksListResource):
    """Works capabilities bound to a parent route, e.g. ``members/{id}/works``.

    Obtain instances via the parent's ``works()`` method; scoped routes
    accept the full works list parameter set and count as single-record
    requests for Crossref rate limiting. Single-work methods (``get``,
    ``exists``, ``agency``, ``latest_version``) are omitted because Crossref
    serves them only at ``/works/{doi}``.
    """


__all__ = ["ScopedWorksResource", "WorksResource"]
