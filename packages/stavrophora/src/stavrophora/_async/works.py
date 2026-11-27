"""Works resources: the top-level ``/works`` route and parent-scoped works."""

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from bibliofabric import OnError, validate_model
from bibliofabric.exceptions import ConfigurationError
from bibliofabric.ids import normalize_doi
from bibliofabric.paging import Page
from pydantic import BaseModel

from ..dialect import CrossrefDialect
from ..filters import WorksFilters
from ..models import Work, WorkAgency
from ..models.base import UpdateTo
from .dialect import CrossrefResourceClient

#: Crossref caps facet value counts at 1000 and ``sample`` at 100.
MAX_FACET_COUNT = 1000
MAX_SAMPLE = 100


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


class WorksResource(CrossrefResourceClient[Work]):
    """Typed client for the Crossref ``/works`` route."""

    path = "works"
    model = Work
    dialect = CrossrefDialect
    filters_model = WorksFilters
    supports_query = True
    supports_filter = True
    supports_sort = True
    supports_select = True
    batch_size = 50

    def normalize_id(self, value: str | int) -> str:
        """Return the bare lowercase DOI (DOIs are case-insensitive)."""
        return normalize_doi(str(value))

    async def latest_version(self, doi: str) -> Work:
        """Resolve a DOI to the newest record in its Crossmark update chain.

        Older records of an update chain carry ``updated-by`` entries naming
        the works that updated them, each with a timestamp or date parts.
        This follows the entry with the latest date until a record carries no
        further updates and returns it. A DOI without update data is returned
        unchanged after one request.
        """
        work = await self.get(doi)
        seen = {self.normalize_id(doi)}
        if work.doi:
            seen.add(self.normalize_id(work.doi))
        while work.updated_by:
            newest = max(work.updated_by, key=_update_timestamp)
            target = newest.doi
            if not target or self.normalize_id(target) in seen:
                break
            seen.add(self.normalize_id(target))
            work = await self.get(target)
            if work.doi:
                seen.add(self.normalize_id(work.doi))
        return work

    async def agency(self, doi: str) -> WorkAgency:
        """Look up the DOI registration agency for a work."""
        response = await self._client.request("GET", f"{self.item_path(doi)}/agency")
        data = self._client.unwrapper.item(self._client.parse_json(response))
        return validate_model(
            WorkAgency, data, request=response.request, response=response
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
        query_params = self._search_params(
            filters=filters, query=query, page=1, page_size=0, params=params
        )
        query_params["facet"] = self._facet_param(facets, count)
        page = await self._request_page(query_params, page=1)
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
        query_params = self._search_params(
            filters=filters, query=query, select=select, params=params
        )
        query_params.pop(self.dialect.page_size_param, None)
        query_params.pop(self.dialect.offset_param, None)
        query_params["sample"] = n
        return await self._request_page(query_params, page=None)

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


class ScopedWorksResource(WorksResource):
    """Works capabilities bound to a parent route, e.g. ``members/{id}/works``.

    Obtain instances via the parent's ``works()`` method; scoped routes
    accept the full works parameter set but count as single-record requests
    for Crossref rate limiting. Single-work lookups are rejected client-side
    because Crossref only serves them at ``/works/{doi}``.
    """

    async def get(
        self,
        id: str | int,
        *,
        select: Sequence[str] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Work:
        """Not supported: Crossref serves single works only at ``/works/{doi}``."""
        raise ConfigurationError(
            f"Crossref has no single-work route under /{self.path}; "
            "use client.works.get(doi)."
        )

    async def exists(self, id: str | int) -> bool:
        """Not supported: Crossref serves existence checks only at ``/works/{doi}``."""
        raise ConfigurationError(
            f"Crossref has no single-work route under /{self.path}; "
            "use client.works.exists(doi)."
        )

    async def agency(self, doi: str) -> WorkAgency:
        """Not supported: Crossref serves agency lookups only at ``/works/{doi}/agency``."""
        raise ConfigurationError(
            f"Crossref has no agency route under /{self.path}; "
            "use client.works.agency(doi)."
        )

    async def latest_version(self, doi: str) -> Work:
        """Not supported: Crossref serves single works only at ``/works/{doi}``."""
        raise ConfigurationError(
            f"Crossref has no single-work route under /{self.path}; "
            "use client.works.latest_version(doi)."
        )
