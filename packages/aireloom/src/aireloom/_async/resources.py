"""Resource clients for the OpenAIRE Graph and Scholexplorer APIs."""

import logging
from collections.abc import AsyncIterator, Callable, Mapping, Sequence
from typing import Any, ClassVar
from urllib.parse import quote

from bibliofabric import BaseApiClient, OnError, ResourceClient
from bibliofabric.exceptions import ConfigurationError
from bibliofabric.ids import normalize_doi, normalize_orcid
from bibliofabric.paging import Page, QueryDialect
from pydantic import BaseModel, ValidationError as PydanticValidationError

from ..dialect import GRAPH_DIALECT, LINKS_DIALECT, SCHOLIX_DIALECT
from ..filters import (
    DataSourcesFilters,
    GraphFilters,
    LinksFilters,
    OrganizationsFilters,
    PersonsFilters,
    ProjectsFilters,
    ResearchProductsFilters,
    ScholixFilters,
    encode_filter_value,
)
from ..models import (
    DataSource,
    Organization,
    Person,
    Project,
    Relation,
    RelationInfo,
    ResearchProduct,
    ScholixLinkProvider,
    ScholixPublisher,
    ScholixRelationship,
)

logger = logging.getLogger(__name__)


class GraphResource[E: BaseModel](ResourceClient[E]):
    """Base for the five V4 entity endpoints.

    Sends all filter criteria as one V4 ``filter`` expression, validates sort
    fields per entity, serves single-entity ``get()`` through the V3 by-id
    route (V4 has none), and exposes typed ``facets``/``group_by`` helpers.
    """

    dialect: ClassVar[QueryDialect] = GRAPH_DIALECT
    sort_fields: ClassVar[frozenset[str]] = frozenset({"relevance"})

    def build_filter_params(
        self, filters: BaseModel | Mapping[str, Any] | None
    ) -> dict[str, str]:
        """Convert filter criteria into the single V4 ``filter`` parameter.

        A ``GraphFilters`` model or a plain mapping both become ``field:value``
        entries joined with commas; list values become pipe-separated ORs.
        """
        if filters is None:
            return {}
        if isinstance(filters, Mapping):
            expression = ",".join(
                f"{field}:{encode_filter_value(value)}"
                for field, value in filters.items()
                if value is not None
            )
            return {"filter": expression} if expression else {}
        if isinstance(filters, GraphFilters):
            return {"filter": filters.to_expression()}
        dumped = filters.model_dump(exclude_none=True, by_alias=True)
        expression = ",".join(
            f"{field}:{encode_filter_value(value)}" for field, value in dumped.items()
        )
        return {"filter": expression} if expression else {}

    def format_sort(self, sort: str | Sequence[str]) -> dict[str, str]:
        """Validate sort fields against the entity's allowed fields.

        Accepts ``"citation_count:desc"`` or a list of such entries; the
        direction is optional and defaults to the API default.
        """
        if self.dialect.sort_param is None:
            return {}
        entries = [sort] if isinstance(sort, str) else list(sort)
        normalized: list[str] = []
        for entry in entries:
            for raw in entry.split(","):
                piece = raw.strip()
                if not piece:
                    continue
                field, has_dir, direction = piece.partition(":")
                if field not in self.sort_fields:
                    valid = ", ".join(sorted(self.sort_fields))
                    raise ConfigurationError(
                        f"Invalid sort field {field!r} for {type(self).__name__}. "
                        f"Valid fields: {valid}."
                    )
                if has_dir and direction.strip().lower() not in ("asc", "desc"):
                    raise ConfigurationError(
                        f"Invalid sort direction {direction!r}; use asc or desc."
                    )
                normalized.append(
                    f"{field}:{direction.strip().lower()}" if has_dir else field
                )
        return {self.dialect.sort_param: ",".join(normalized)}

    def build_batch_params(self, field: str, values: Sequence[str]) -> dict[str, Any]:
        """Encode one batch chunk as a V4 OR expression: ``field:a|b|c``."""
        return {"filter": f"{field}:{'|'.join(values)}"}

    def item_path(self, id: str) -> str:
        """Return the V3 by-id path for ``id``; V4 has no by-id route.

        Colons stay unencoded: the V3 by-id routes expect the raw
        ``prefix::suffix`` identifiers and reject the percent-encoded form.
        """
        entity = self.path.partition("/")[2]
        return f"v3/{entity}/{quote(self.normalize_id(id), safe=':')}"

    async def facets(
        self,
        *fields: str,
        filters: BaseModel | Mapping[str, Any] | None = None,
        query: str | None = None,
        page_size: int | None = None,
    ) -> dict[str, dict[str, int]]:
        """Return facet counts per field: ``{field: {value: count}}``.

        Requests records plus aggregations, so pass ``page_size`` to bound
        the record part (the API default page size applies otherwise).
        """
        page = await self.search(
            filters,
            query=query,
            page_size=page_size,
            params={"facets": ",".join(fields)},
        )
        raw = page.meta.get("facets") or {}
        return {
            field: {value: int(count) for value, count in buckets.items()}
            for field, buckets in raw.items()
            if isinstance(buckets, dict)
        }

    async def group_by(
        self,
        field: str,
        *,
        filters: BaseModel | Mapping[str, Any] | None = None,
        query: str | None = None,
    ) -> dict[str, int]:
        """Return counts per value of ``field`` without fetching records.

        ``group_by`` is an aggregation-only mode: the response carries counts
        and an empty ``results`` list.
        """
        page = await self.search(
            filters, query=query, page_size=1, params={"group_by": field}
        )
        raw = (page.meta.get("facets") or {}).get(field)
        if not isinstance(raw, dict):
            return {}
        return {value: int(count) for value, count in raw.items()}


class DataSourcesResource(GraphResource[DataSource]):
    """V4 data sources endpoint: search, iterate, count, facets, group_by.

    ``get(id)`` reads the V3 by-id route because V4 has no by-id endpoints.
    """

    path = "v4/datasources"
    model = DataSource
    filters_model = DataSourcesFilters


class OrganizationsResource(GraphResource[Organization]):
    """V4 organizations endpoint: search, iterate, count, facets, group_by.

    ``get(id)`` reads the V3 by-id route because V4 has no by-id endpoints.
    """

    path = "v4/organizations"
    model = Organization
    filters_model = OrganizationsFilters

    async def find_variants(
        self, names: Sequence[str], *, country: str | None = None
    ) -> list[Organization]:
        """Search each name fragment and return deduplicated organizations.

        Records are deduplicated by exact ``id`` keeping the first match;
        ``pending_org_::`` records are kept on purpose. They carry
        organization-project links that the canonical merged record lost,
        which makes them the main source of undercounted org-project
        links, so callers decide how to merge them.
        """
        filters = {"country": country} if country else None
        found: dict[str, Organization] = {}
        for name in names:
            page = await self.search(filters, query=name)
            for org in page.results:
                found.setdefault(org.id, org)
        return list(found.values())


class PersonsResource(GraphResource[Person]):
    """V4 persons endpoint: search, iterate, count, facets, group_by.

    ``get(id)`` reads the V3 by-id route because V4 has no by-id endpoints.
    """

    path = "v4/persons"
    model = Person
    filters_model = PersonsFilters


class ProjectsResource(GraphResource[Project]):
    """V4 projects endpoint: search, iterate, count, facets, group_by.

    ``get(id)`` reads the V3 by-id route because V4 has no by-id endpoints.
    """

    path = "v4/projects"
    model = Project
    filters_model = ProjectsFilters
    sort_fields = frozenset({"relevance", "start_date", "end_date"})


class LinksResource(ResourceClient[Relation]):
    """``/v3/research-products/links``: relations between research products.

    This route has no cursor and no sort parameter. Page windows are therefore
    not pinned: if the result ordering changes between requests, pages can
    shift and relations can be skipped or duplicated. The iterator stops on an
    empty page or when the reported total has been fetched, which bounds the
    walk but cannot remove that upstream hazard.
    """

    path = "v3/research-products/links"
    model = Relation
    dialect = LINKS_DIALECT
    filters_model = LinksFilters
    batch_size = 0

    async def get_relations_info(self) -> list[RelationInfo]:
        """Return the relation types the links endpoint can produce."""
        response = await self._client.request("GET", f"{self.path}/relations-info")
        info: list[RelationInfo] = []
        for entry in response.json():
            try:
                info.append(RelationInfo.model_validate(entry))
            except PydanticValidationError as error:
                logger.warning("Skipping invalid relations-info entry: %s", error)
        return info

    def build_filter_params(
        self, filters: BaseModel | Mapping[str, Any] | None
    ) -> dict[str, Any]:
        """Dump ``LinksFilters`` as individual query parameters."""
        if filters is None:
            return {}
        if isinstance(filters, LinksFilters):
            return {
                key: str(value)
                for key, value in filters.model_dump(exclude_none=True).items()
            }
        return dict(filters)


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
    """Scholix link search over the Scholexplorer host (V3, V2 for dates).

    Backed by a dedicated internal API client for ``api.scholexplorer.openaire.eu``
    that shares the Graph client's credentials and settings but throttles
    itself to one request per second (the host sends no rate-limit headers).

    V3 is the default surface. The V2 endpoint stays available and serves any
    query that carries date filters, because the V3 endpoint accepts ``from``
    and ``to`` but returns zero rows for every value (server-side regression,
    OA-4).
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
