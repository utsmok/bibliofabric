"""Client for the OpenAlex works endpoint."""

from collections.abc import Mapping, Sequence
from typing import Any, Literal, TypedDict, Unpack, override

from bibliofabric import OnError
from bibliofabric.exceptions import ConfigurationError
from bibliofabric.paging import Page
from pydantic import BaseModel

from ..models import Work
from .dialect import OpenAlexResourceClient

VALID_CORPUS_VALUES = ("core", "expansion", "all")
SEARCH_SCOPES = (
    "title",
    "title_and_abstract",
    "title_abstract_keywords",
    "exact",
    "semantic",
)


def _merge_works_params(
    params: Mapping[str, Any] | None,
    *,
    corpus: Literal["core", "expansion", "all"] | None = None,
    include_parts: bool | None = None,
    include_pulled: bool | None = None,
    rerank: bool = False,
) -> dict[str, Any] | None:
    """Validate works-only query controls and merge them into ``params``."""
    extra = dict(params or {})
    if corpus is not None:
        if corpus not in VALID_CORPUS_VALUES:
            raise ConfigurationError(
                f"corpus must be one of {VALID_CORPUS_VALUES}, got {corpus!r}."
            )
        extra["corpus"] = corpus
    if include_parts is not None:
        extra["include_parts"] = str(include_parts).lower()
    if include_pulled is not None:
        extra["include_pulled"] = str(include_pulled).lower()
    if rerank:
        extra["rerank"] = "true"
    return extra or None


class _WorksSearchKwargs(TypedDict, total=False):
    sort: str | Sequence[str] | None
    select: Sequence[str] | None
    page: int | None
    page_size: int | None
    cursor: str | None
    corpus: Literal["core", "expansion", "all"] | None
    include_parts: bool | None
    include_pulled: bool | None
    rerank: bool
    on_error: OnError
    failures: list[tuple[dict[str, Any], Exception]] | None


class WorksClient(OpenAlexResourceClient[Work]):
    """Client for the ``/works`` endpoint.

    Adds the works-only query features: ``corpus``/``include_pulled``/
    ``include_parts``, corpus-aware ``sample()``, the scoped ``search.*``
    parameters, and DOI-based batch retrieval.
    """

    path = "works"
    model = Work

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
        corpus: Literal["core", "expansion", "all"] | None = None,
        include_parts: bool | None = None,
        include_pulled: bool | None = None,
        rerank: bool = False,
    ) -> Page[Work]:
        """Search works; accepts the works-only corpus controls.

        ``corpus`` selects which works answer: ``core`` (default upstream)
        excludes pulled and part works, ``expansion`` is the expansion set,
        ``all`` is everything. ``include_parts``/``include_pulled`` re-add
        those subsets to ``core``. Note that a ``is_pulled``/``is_retracted``
        filter re-includes pulled works on its own.

        ``rerank=True`` reorders the top 100 of a relevance-sorted search
        (costs 10 extra credits and requires the relevance sort a ``query``
        gives you); ``page.meta["reranked"]`` reports whether it applied.
        """
        extra = _merge_works_params(
            params,
            corpus=corpus,
            include_parts=include_parts,
            include_pulled=include_pulled,
            rerank=rerank,
        )
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
            params=extra,
        )

    async def search_scoped(
        self,
        text: str,
        *,
        scope: Literal[
            "title",
            "title_and_abstract",
            "title_abstract_keywords",
            "exact",
            "semantic",
        ] = "title_and_abstract",
        filters: BaseModel | Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
        **kwargs: Unpack[_WorksSearchKwargs],
    ) -> Page[Work]:
        """Search works under one scoped ``search.*`` parameter.

        Scopes: ``title``, ``title_and_abstract``, ``title_abstract_keywords``,
        ``exact`` (supports wildcards and proximity operators), and
        ``semantic`` (embedding search; max 50 results, 1 request/second, and
        only its whitelisted filters combine). Only one search parameter is
        allowed per request; a search costs 10 credits.
        """
        if scope not in SEARCH_SCOPES:
            raise ConfigurationError(
                f"scope must be one of {SEARCH_SCOPES}, got {scope!r}."
            )
        merged = {**(params or {}), f"search.{scope}": text}
        return await self.search(filters, params=merged, **kwargs)

    @override
    async def sample(
        self,
        n: int,
        *,
        seed: int | None = None,
        filters: BaseModel | Mapping[str, Any] | None = None,
        query: str | None = None,
        sort: str | Sequence[str] | None = None,
        select: Sequence[str] | None = None,
        page: int | None = None,
        page_size: int | None = None,
        cursor: str | None = None,
        on_error: OnError = "raise",
        failures: list[tuple[dict[str, Any], Exception]] | None = None,
        params: Mapping[str, Any] | None = None,
        corpus: Literal["core", "expansion", "all"] | None = None,
        include_parts: bool | None = None,
        include_pulled: bool | None = None,
        rerank: bool = False,
    ) -> Page[Work]:
        """Return a random sample of up to ``n`` works (max 10,000).

        Pass ``seed`` for reproducibility, and works-only ``corpus`` /
        ``include_parts`` / ``include_pulled`` / ``rerank`` controls.
        ``Page.total`` reports the sample size, not the size of the filtered
        corpus.
        """
        merged = _merge_works_params(
            params,
            corpus=corpus,
            include_parts=include_parts,
            include_pulled=include_pulled,
            rerank=rerank,
        )
        return await super().sample(
            n,
            seed=seed,
            filters=filters,
            query=query,
            sort=sort,
            select=select,
            page=page,
            page_size=page_size,
            cursor=cursor,
            on_error=on_error,
            failures=failures,
            params=merged,
        )

    async def batch_get_by_doi(
        self, dois: Sequence[str], *, batch_size: int | None = None
    ) -> dict[str, Work]:
        """Fetch works by DOI, batched as pipe-joined OR filters.

        DOIs are normalized (URL prefixes stripped, lowercased) and split
        into chunks of ``batch_size`` (default 100, the OpenAlex OR cap).
        Returns ``{normalized doi: Work}``; DOIs not found are absent.
        """
        return await self.batch_get(dois, field="doi", batch_size=batch_size)

    async def batch_get_by_openalex_id(
        self, ids: Sequence[str], *, batch_size: int | None = None
    ) -> dict[str, Work]:
        """Fetch works by OpenAlex id (bare ``W...`` or full URL)."""
        return await self.batch_get(ids, field="id", batch_size=batch_size)

    async def oa_pdf_urls(self, doi_or_id: str) -> list[str]:
        """Return downloadable PDF URLs for a work, best OA copy first.

        Reads ``pdf_url`` from ``best_oa_location``, then
        ``primary_location``, then the remaining ``locations``; duplicates
        keep their first position. Returns ``[]`` when no location carries a
        PDF. OpenAlex's own paid PDF copies (``content_urls.pdf``) are not
        included.
        """
        work = await self.get(doi_or_id)
        urls: list[str] = []
        seen: set[str] = set()
        for location in (work.best_oa_location, work.primary_location, *work.locations):
            pdf = location.pdf_url if location is not None else None
            if pdf is None or pdf in seen:
                continue
            seen.add(pdf)
            urls.append(str(pdf))
        return urls

    async def citing(
        self,
        work_id: str,
        *,
        limit: int = 100,
        filters: BaseModel | Mapping[str, Any] | None = None,
        sort: str | Sequence[str] | None = None,
    ) -> list[Work]:
        """Collect works that cite ``work_id``, bounded by ``limit``."""
        merged: dict[str, Any] = {}
        if filters is not None:
            extra = (
                filters.model_dump(exclude_none=True, by_alias=True)
                if isinstance(filters, BaseModel)
                else {k: v for k, v in filters.items() if v is not None}
            )
            merged.update(extra)
        merged["cites"] = self.normalize_id(work_id)
        return await self.collect(merged, sort=sort, limit=limit)

    async def referenced(self, work_id: str, *, limit: int = 100) -> list[Work]:
        """Fetch (up to ``limit`` of) the works referenced by ``work_id``."""
        if limit <= 0:
            raise ConfigurationError(f"limit must be positive, got {limit}.")
        work = await self.get(work_id)
        targets = [self.normalize_id(target) for target in work.referenced_works]
        targets = targets[:limit]
        if not targets:
            return []
        results = await self.batch_get(targets, field="id")
        return [results[target] for target in targets if target in results]
