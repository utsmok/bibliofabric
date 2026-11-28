"""Client for the Semantic Scholar paper endpoints."""

from collections.abc import AsyncIterator, Mapping, Sequence
from typing import Any, override

from bibliofabric import OnError, validate_model
from bibliofabric.exceptions import ConfigurationError, NotFoundError
from bibliofabric.paging import Page
from pydantic import BaseModel

from ..dialect import BULK_SEARCH_MAX_LIMIT, PAPER_BATCH_MAX_IDS
from ..filters import PaperSearchFilters
from ..models import (
    Author,
    AutocompletePaper,
    Citation,
    Paper,
    PaperMatch,
    Reference,
)
from .resources import ScholiastResourceClient, fetch_list_page


def _filter_params(filters: BaseModel | Mapping[str, Any] | None) -> dict[str, Any]:
    """Dump filter criteria into plain query parameters."""
    if filters is None:
        return {}
    if isinstance(filters, BaseModel):
        return filters.model_dump(exclude_none=True)
    return {key: value for key, value in filters.items() if value is not None}


class PapersClient(ScholiastResourceClient[Paper]):
    """Client for the ``/paper`` routes.

    ``get``, ``search``, ``iterate``, ``collect``, ``first``, ``count``,
    and ``exists`` come from the resource base; ``fields`` is the
    ``select`` argument everywhere. ``get`` accepts every id form the API
    documents (``S2 id``, ``DOI:``, ``ARXIV:``, ``PMID:``, ``PMCID:``,
    ``MAG:``, ``ACL:``, ``PubMedCentral:``, ``CorpusId:``, ``URL:``).
    """

    path = "paper"
    model = Paper
    batch_size = PAPER_BATCH_MAX_IDS

    @override
    def search_path(self, query: str | None) -> str:
        """Return ``paper/search``; the query always travels on the search route."""
        return "paper/search"

    @override
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
        fields: Sequence[str] | None = None,
    ) -> Page[Paper]:
        """Fetch one page of relevance-ranked papers.

        ``fields`` selects the returned fields (the API's ``fields``
        parameter; the same list ``select`` accepts).
        """
        return await super().search(
            filters,
            query=query,
            sort=sort,
            select=fields if fields is not None else select,
            page=page,
            page_size=page_size,
            cursor=cursor,
            on_error=on_error,
            failures=failures,
            params=params,
        )

    @override
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
    ) -> dict[str, Paper]:
        """Not supported; the API batches papers only through :meth:`batch`."""
        raise ConfigurationError(
            "PapersClient.batch_get is disabled; use batch(ids=...) instead."
        )

    async def batch(
        self,
        ids: Sequence[str],
        *,
        fields: Sequence[str] | None = None,
    ) -> list[Paper]:
        """Fetch many papers in one or more ``POST /paper/batch`` calls.

        Ids use the same forms as :meth:`get`. The API answers ``null``
        for unknown ids; those entries are dropped. Requests chunk at 500
        ids (the API maximum) and are sent with retries.
        """
        results: list[Paper] = []
        keys = list(dict.fromkeys(ids))
        if not keys:
            return results
        for start in range(0, len(keys), PAPER_BATCH_MAX_IDS):
            chunk = keys[start : start + PAPER_BATCH_MAX_IDS]
            params = {"fields": ",".join(fields)} if fields else None
            response = await self._client.request(
                "POST",
                "paper/batch",
                params=params,
                json={"ids": chunk},
                retry=True,
            )
            body = self._client.parse_json(response)
            records = (
                body
                if isinstance(body, list)
                else (body.get("data") if isinstance(body, dict) else None)
            )
            if not isinstance(records, list):
                raise ConfigurationError(
                    "POST /paper/batch answered without a record list."
                )
            for record in records:
                if record is None:
                    continue
                results.append(
                    validate_model(
                        Paper,
                        record,
                        request=getattr(response, "request", None),
                        response=response,
                    )
                )
        return results

    async def bulk_search(
        self,
        query: str | None = None,
        filters: PaperSearchFilters | Mapping[str, Any] | None = None,
        *,
        fields: Sequence[str] | None = None,
        limit: int | None = None,
        token: str | None = None,
    ) -> Page[Paper]:
        """Fetch one page of up to 1000 papers from ``/paper/search/bulk``.

        Bulk search returns basic paper data ordered by corpus id, not by
        relevance. When more papers match, ``page.next_cursor`` carries
        the continuation token; pass it back as ``token``.
        """
        params = _filter_params(filters)
        if query:
            params["query"] = query
        if fields:
            params["fields"] = ",".join(fields)
        if limit is not None:
            if limit > BULK_SEARCH_MAX_LIMIT:
                raise ConfigurationError(
                    f"bulk search allows at most {BULK_SEARCH_MAX_LIMIT} per call, "
                    f"got {limit}."
                )
            params["limit"] = limit
        if token is not None:
            params["token"] = token
        response = await self._client.request("GET", "paper/search/bulk", params=params)
        body = self._client.parse_json(response)
        unwrapper = self._client.unwrapper
        results = self._validate_records(
            unwrapper.results(body),
            on_error="raise",
            failures=None,
            request=getattr(response, "request", None),
            response=response,
        )
        return Page(
            results=results,
            total=unwrapper.total(body),
            next_cursor=unwrapper.next_cursor(body),
            page=None,
            meta=unwrapper.meta(body),
        )

    def bulk_iterate(
        self,
        query: str | None = None,
        filters: PaperSearchFilters | Mapping[str, Any] | None = None,
        *,
        fields: Sequence[str] | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[Paper]:
        """Iterate over every matching paper by following the bulk token."""
        return self._bulk_iterate(query, filters, fields=fields, limit=limit)

    async def _bulk_iterate(
        self,
        query: str | None,
        filters: PaperSearchFilters | Mapping[str, Any] | None,
        *,
        fields: Sequence[str] | None,
        limit: int | None,
    ) -> AsyncIterator[Paper]:
        token: str | None = None
        seen = 0
        while True:
            page = await self.bulk_search(
                query, filters, fields=fields, limit=limit, token=token
            )
            for paper in page.results:
                yield paper
                seen += 1
                if limit is not None and seen >= limit:
                    return
            token = page.next_cursor
            if token is None:
                return

    async def citations(
        self,
        id: str,
        *,
        fields: Sequence[str] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Page[Citation]:
        """Fetch one page of the papers citing ``id``.

        Each record carries the citing paper plus ``contexts``,
        ``intents``, ``contextsWithIntent``, and ``isInfluential``.
        ``page.next_cursor`` is the next offset, or ``None`` on the last
        page. Note that the papers of an author see only their most
        recent 10,000 citation and reference edges.
        """
        return await fetch_list_page(
            self._client,
            f"paper/{id}/citations",
            Citation,
            fields=fields,
            limit=limit,
            offset=offset,
        )

    async def references(
        self,
        id: str,
        *,
        fields: Sequence[str] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Page[Reference]:
        """Fetch one page of the papers ``id`` cites.

        Each record carries the cited paper plus the citation contexts of
        the source paper.
        """
        return await fetch_list_page(
            self._client,
            f"paper/{id}/references",
            Reference,
            fields=fields,
            limit=limit,
            offset=offset,
        )

    async def authors(
        self,
        id: str,
        *,
        fields: Sequence[str] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Page[Author]:
        """Fetch one page of the authors of ``id``."""
        return await fetch_list_page(
            self._client,
            f"paper/{id}/authors",
            Author,
            fields=fields,
            limit=limit,
            offset=offset,
        )

    async def autocomplete(self, query: str) -> list[AutocompletePaper]:
        """Return completion candidates for a partial query.

        Candidates carry a minimal record (``id``, ``title``,
        ``authorsYear``). The API returns an empty list for no matches.
        """
        text = query.strip()
        if not text:
            raise ConfigurationError("query must be a non-empty string.")
        response = await self._client.request(
            "GET", "paper/autocomplete", params={"query": text}
        )
        body = self._client.parse_json(response)
        return [
            validate_model(
                AutocompletePaper,
                record,
                request=getattr(response, "request", None),
                response=response,
            )
            for record in self._client.unwrapper.results(body)
        ]

    async def search_match(
        self,
        query: str,
        *,
        fields: Sequence[str] | None = None,
    ) -> PaperMatch:
        """Return the paper whose title matches ``query`` best.

        Raises :class:`NotFoundError` when no candidate passes the
        relevance threshold. ``matchScore`` sits on the returned match.
        """
        text = query.strip()
        if not text:
            raise ConfigurationError("query must be a non-empty string.")
        params: dict[str, Any] = {"query": text}
        if fields:
            params["fields"] = ",".join(fields)
        response = await self._client.request(
            "GET", "paper/search/match", params=params
        )
        body = self._client.parse_json(response)
        records = [
            record
            for record in self._client.unwrapper.results(body)
            if isinstance(record, dict)
        ]
        if not records:
            raise NotFoundError(
                f"No paper matches the title {text!r}.",
                request=getattr(response, "request", None),
                response=response,
            )
        return PaperMatch.from_record(records[0])
