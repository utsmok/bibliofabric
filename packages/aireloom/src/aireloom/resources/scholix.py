"""Resource facade for the Scholexplorer API (Scholix links).

V3 is the default surface. The V2 endpoint stays available and serves any
query that carries date filters, because the V3 endpoint accepts ``from`` and
``to`` but returns zero rows for every value (server-side regression, OA-4).
"""

import logging
from collections.abc import AsyncIterator, Callable
from typing import Any

from bibliofabric.client import BaseApiClient
from bibliofabric.paging import Page
from bibliofabric.resources import OnError, ResourceClient

from ..dialect import SCHOLIX_DIALECT
from ..filters import ScholixFilters
from ..models import ScholixLinkProvider, ScholixPublisher, ScholixRelationship

logger = logging.getLogger(__name__)


def _records(payload: Any) -> list[Any]:
    """Extract the record list from the shapes the listing endpoints return."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for value in payload.values():
            if isinstance(value, list):
                return value
    return []


class _ScholixLinks(ResourceClient[ScholixRelationship]):
    """One version of the Scholexplorer ``Links`` endpoint."""

    model = ScholixRelationship
    dialect = SCHOLIX_DIALECT
    filters_model = ScholixFilters
    batch_size = 0


class ScholixV3Links(_ScholixLinks):
    """``/v3/Links``."""

    path = "v3/Links"


class ScholixV2Links(_ScholixLinks):
    """``/v2/Links``."""

    path = "v2/Links"


class ScholixResource:
    """Scholix link search over the Scholexplorer host.

    Backed by a dedicated internal API client for ``api.scholexplorer.openaire.eu``
    that shares the Graph client's credentials and settings but throttles
    itself to one request per second (the host sends no rate-limit headers).

    Date filters (``from_date``/``to_date``) are routed to V2 automatically:
    the V3 endpoint accepts them but returns zero rows for every value (OA-4).
    """

    def __init__(self, client: BaseApiClient) -> None:
        self._v3 = ScholixV3Links(client)
        self._v2 = ScholixV2Links(client)
        self._client = client

    @staticmethod
    def _has_date_filter(filters: ScholixFilters | None) -> bool:
        return filters is not None and not (
            filters.from_date is None and filters.to_date is None
        )

    async def search_links(
        self,
        filters: ScholixFilters | None = None,
        *,
        page: int | None = None,
        page_size: int | None = None,
    ) -> Page[ScholixRelationship]:
        """Fetch one page of links as typed records.

        Queries with ``from_date`` or ``to_date`` are served by V2, where the
        date filters actually work; everything else goes to V3.
        """
        target = self._v2 if self._has_date_filter(filters) else self._v3
        return await target.search(filters, page=page, page_size=page_size)

    def iterate_links(
        self,
        filters: ScholixFilters | None = None,
        *,
        page_size: int | None = None,
        limit: int | None = None,
        on_error: OnError = "raise",
        failures: list[tuple[dict[str, Any], Exception]] | None = None,
        on_page: Callable[[int, str | None], Any] | None = None,
    ) -> AsyncIterator[ScholixRelationship]:
        """Iterate over all matching links, 99 per page.

        Queries with date filters go to V2 (see :meth:`search_links`). The
        route has no cursor, so page windows are not pinned; the iterator
        stops on an empty page or when the reported total has been fetched.
        """
        target = self._v2 if self._has_date_filter(filters) else self._v3
        return target.iterate(
            filters,
            page_size=page_size,
            limit=limit,
            on_error=on_error,
            failures=failures,
            on_page=on_page,
        )

    async def search_links_v2(
        self,
        filters: ScholixFilters | None = None,
        *,
        page: int | None = None,
        page_size: int | None = None,
    ) -> Page[ScholixRelationship]:
        """Fetch one page of links from the V2 endpoint."""
        return await self._v2.search(filters, page=page, page_size=page_size)

    def iterate_links_v2(
        self,
        filters: ScholixFilters | None = None,
        *,
        page_size: int | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[ScholixRelationship]:
        """Iterate over all matching links from the V2 endpoint."""
        return self._v2.iterate(filters, page_size=page_size, limit=limit)

    async def list_link_providers(
        self, name: str | None = None
    ) -> list[ScholixLinkProvider]:
        """List Scholexplorer link providers (V2)."""
        params = {"name": name} if name is not None else None
        payload = await self._client.get_json("v2/LinkProvider", params=params)
        return [
            ScholixLinkProvider.model_validate(entry) for entry in _records(payload)
        ]

    async def list_link_publishers(
        self, *, in_target: bool = True, name: str | None = None
    ) -> list[ScholixPublisher]:
        """List publishers of source or target objects (V2)."""
        path = "v2/LinkPublisher/inTarget" if in_target else "v2/LinkPublisher/inSource"
        params = {"name": name} if name is not None else None
        payload = await self._client.get_json(path, params=params)
        return [ScholixPublisher.model_validate(entry) for entry in _records(payload)]

    async def get_kpi(self) -> str:
        """Return the Scholexplorer Prometheus KPI document."""
        response = await self._client.request("GET", "kpi/getKPI")
        return response.text
