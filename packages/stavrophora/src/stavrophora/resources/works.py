"""Works resources: the top-level ``/works`` route and parent-scoped works."""

from collections.abc import Mapping, Sequence
from typing import Any

from bibliofabric.exceptions import ConfigurationError, NotFoundError
from bibliofabric.ids import normalize_doi
from bibliofabric.paging import Page
from pydantic import BaseModel

from ..dialect import CrossrefResourceClient
from ..filters import WorksFilters
from ..models import Work, WorkAgency

#: Crossref caps facet value counts at 1000 and ``sample`` at 100.
MAX_FACET_COUNT = 1000
MAX_SAMPLE = 100


class WorksResource(CrossrefResourceClient[Work]):
    """Typed client for the Crossref ``/works`` route."""

    path = "works"
    model = Work
    filters_model = WorksFilters
    supports_query = True
    supports_filter = True
    supports_sort = True
    supports_select = True
    batch_size = 50

    def normalize_id(self, value: str | int) -> str:
        """Return the bare lowercase DOI (DOIs are case-insensitive)."""
        return normalize_doi(str(value))

    async def exists(self, doi: str) -> bool:
        """Return True when the DOI is registered at Crossref.

        Sends a HEAD request, which Crossref documents as an existence
        check, so no record body is transferred. Unknown DOIs answer 404
        and return False.
        """
        try:
            await self._client.request("HEAD", self.item_path(doi))
        except NotFoundError:
            return False
        return True

    async def latest_version(self, doi: str) -> Work:
        """Resolve a DOI to the newest record in its Crossmark update chain.

        Older records of an update chain carry ``updated-by`` entries naming
        the works that updated them, each with a timestamp. This follows the
        entry with the latest timestamp until a record carries no further
        updates and returns it. A DOI without update data is returned
        unchanged after one request.
        """
        work = await self.get(doi)
        seen = {self.normalize_id(doi)}
        while work.updated_by:
            newest = max(
                work.updated_by,
                key=lambda entry: (
                    (entry.updated.timestamp or 0) if entry.updated else 0
                ),
            )
            target = newest.doi
            if not target or self.normalize_id(target) in seen:
                break
            seen.add(self.normalize_id(target))
            work = await self.get(target)
        return work

    async def agency(self, doi: str) -> WorkAgency:
        """Look up the DOI registration agency for a work."""
        response = await self._client.request("GET", f"{self.item_path(doi)}/agency")
        data = self._client.unwrapper.item(response.json())
        return WorkAgency.model_validate(data)

    async def batch_get_by_doi(
        self,
        dois: Sequence[str],
        *,
        batch_size: int | None = None,
        concurrency: int = 4,
    ) -> dict[str, Work]:
        """Fetch many works by DOI in bounded, concurrent filter batches.

        Uses Crossref's repeated-key OR syntax (``filter=doi:a,doi:b``) with
        up to 50 DOIs per request. Returns a dict keyed by bare lowercase
        DOI; DOIs not found are absent.
        """
        return await self.batch_get(
            dois, field="doi", batch_size=batch_size, concurrency=concurrency
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

        Requests the given facet names (``*`` for all) plus at most one
        result row, and returns ``{facet_name: {value: count}}``. ``count``
        caps the values per facet (Crossref allows up to 1000); the API also
        reports a ``value-count`` per facet, which this helper drops.
        """
        if count is not None and not 1 <= count <= MAX_FACET_COUNT:
            raise ConfigurationError(
                f"Facet count must be between 1 and {MAX_FACET_COUNT}, got {count}."
            )
        query_params = self._search_params(
            filters=filters, query=query, page=1, page_size=1, params=params
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
        params: Mapping[str, Any] | None = None,
    ) -> Page[Work]:
        """Fetch one page of works; ``params`` carries extras such as
        ``{"query.title": "...", "sample": 50}`` (works accepts the
        ``query.*`` sub-fields; other routes take plain ``query`` only)."""
        return await super().search(
            filters,
            query=query,
            sort=sort,
            select=select,
            page=page,
            page_size=page_size,
            cursor=cursor,
            params=params,
        )


class ScopedWorksResource(WorksResource):
    """Works capabilities bound to a parent route, e.g. ``members/{id}/works``.

    Obtain instances via the parent's ``works()`` method; scoped routes
    accept the full works parameter set but count as single-record requests
    for Crossref rate limiting.
    """
