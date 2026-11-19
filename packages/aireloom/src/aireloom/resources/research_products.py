"""Resource client for OpenAIRE research products (V4) plus the links route."""

import logging
from collections.abc import AsyncIterator, Callable, Sequence
from typing import Any

from bibliofabric import BaseApiClient, OnError
from bibliofabric.ids import normalize_doi, normalize_orcid
from bibliofabric.paging import Page

from ..filters import LinksFilters, ResearchProductsFilters
from ..models import Relation, RelationInfo, ResearchProduct
from .base import GraphResource
from .links import LinksResource

logger = logging.getLogger(__name__)


class ResearchProductsResource(GraphResource[ResearchProduct]):
    """V4 research products endpoint: search, iterate, count, facets, group_by.

    ``get(id)`` reads the V3 by-id route because V4 has no by-id endpoints.
    Batch lookups use OR expressions over ``id`` and ``ids.doi``.
    """

    path = "v4/research-products"
    model = ResearchProduct
    filters_model = ResearchProductsFilters
    sort_fields = frozenset(
        {
            "relevance",
            "publication_date",
            "date_of_collection",
            "citation_count",
            "influence",
            "popularity",
            "impulse",
        }
    )
    batch_size = 50

    def __init__(self, client: BaseApiClient, links: LinksResource) -> None:
        super().__init__(client)
        self._links = links

    def record_keys(self, entity: ResearchProduct, field: str) -> list[str]:
        if field == "ids.doi":
            # Deduplicated records carry several DOIs; batch_get keeps the requested one.
            return [normalize_doi(doi) for doi in entity.all_dois]
        return super().record_keys(entity, field)

    async def batch_get_by_doi(
        self,
        dois: list[str] | tuple[str, ...],
        *,
        batch_size: int | None = None,
        concurrency: int = 4,
    ) -> dict[str, ResearchProduct]:
        """Fetch research products for many DOIs in bounded, concurrent chunks.

        Keys are bare, lowercased DOIs; missing DOIs are absent from the
        result. The request goes out as ``filter=ids.doi:a|b|c``.
        """
        normalized = list(dict.fromkeys(normalize_doi(doi) for doi in dois))
        return await self.batch_get(
            normalized, field="ids.doi", batch_size=batch_size, concurrency=concurrency
        )

    async def by_orcid(self, orcid: str, *, limit: int = 100) -> list[ResearchProduct]:
        """Return research products whose authorship carries ``orcid``.

        Accepts any spelling ``bibliofabric.ids.normalize_orcid`` handles
        (bare, dashed, or an ``https://orcid.org/`` URL); the filter sends
        the hyphenated form via the V4 ``authorships.author.orcid`` field.
        """
        page = await self.search(
            ResearchProductsFilters(authorships_author_orcid=normalize_orcid(orcid)),
            page_size=limit,
        )
        return page.results

    async def get_fields(
        self, ids: Sequence[str], fields: Sequence[str]
    ) -> list[ResearchProduct]:
        """Sparse-fetch ``fields`` for known ids, ``batch_size`` ids per request.

        Combines the V4 ``select`` parameter with an ``id`` OR-filter
        (verified live on 2026-11-19). The returned records carry only the
        requested fields; every other model field stays at its default.
        """
        wanted = list(dict.fromkeys(ids))
        results: list[ResearchProduct] = []
        for start in range(0, len(wanted), self.batch_size):
            chunk = wanted[start : start + self.batch_size]
            page = await self.search(
                {"id": chunk}, select=list(fields), page_size=len(chunk)
            )
            results.extend(page.results)
        return results

    async def search_links(
        self,
        filters: LinksFilters | None = None,
        *,
        page: int | None = None,
        page_size: int | None = None,
    ) -> Page[Relation]:
        """Fetch one page of relations from the Graph links route."""
        return await self._links.search(filters, page=page, page_size=page_size)

    def iterate_links(
        self,
        filters: LinksFilters | None = None,
        *,
        page_size: int | None = None,
        limit: int | None = None,
        on_error: OnError = "raise",
        failures: list[tuple[dict[str, Any], Exception]] | None = None,
        on_page: Callable[[int, str | None], Any] | None = None,
    ) -> AsyncIterator[Relation]:
        """Iterate over all relations matching ``filters``, 99 per page.

        See :class:`LinksResource` for the missing-sort hazard of this
        page-based route.
        """
        return self._links.iterate(
            filters,
            page_size=page_size,
            limit=limit,
            on_error=on_error,
            failures=failures,
            on_page=on_page,
        )

    async def get_relations_info(self) -> list[RelationInfo]:
        """Return the relation types the links endpoint can produce."""
        return await self._links.get_relations_info()
