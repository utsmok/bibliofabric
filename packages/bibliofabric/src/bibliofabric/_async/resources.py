"""Generic typed resource client over a ``BaseApiClient``.

Subclass :class:`ResourceClient` per endpoint: declare ``path``, ``model``, and
``dialect``, then override the hook methods where the API deviates from the
defaults (filter syntax, sort format, batch parameter shape, id handling).
"""

import logging
from collections.abc import AsyncIterator, Callable, Mapping, Sequence
from typing import Any, ClassVar, Literal
from urllib.parse import quote

from pydantic import BaseModel, ValidationError as PydanticValidationError

from ..exceptions import ConfigurationError, ValidationError
from ..paging import Page, QueryDialect
from ._concurrency import maybe_await, run_bounded
from .client import BaseApiClient

logger = logging.getLogger(__name__)

OnError = Literal["raise", "skip"]


async def _fire_on_page(
    on_page: Callable[[int, str | None], Any] | None,
    page_number: int,
    next_cursor: str | None,
) -> None:
    """Invoke an ``on_page`` callback, awaiting its result if it is awaitable."""
    if on_page is None:
        return
    await maybe_await(on_page(page_number, next_cursor))


class ResourceClient[E: BaseModel]:
    """Typed client for one API resource.

    Class attributes:

    - ``path``: endpoint path relative to the client's base URL, e.g. ``"works"``.
      Pass ``path=`` to the constructor for routes bound to a parent id,
      e.g. ``"members/297/works"``.
    - ``model``: the pydantic model a single entity validates against.
    - ``dialect``: the :class:`QueryDialect` of the API (usually shared).
    - ``filters_model``: optional declaration of the accepted filter model.
    - ``batch_size``: ids per ``batch_get`` chunk; ``0`` disables ``batch_get``.
    """

    path: str
    model: type[E]
    dialect: ClassVar[QueryDialect]
    filters_model: ClassVar[type[BaseModel] | None] = None
    batch_size: ClassVar[int] = 50

    def __init__(self, client: BaseApiClient, *, path: str | None = None) -> None:
        self._client = client
        if path is not None:
            self.path = path

    # --- hooks ---------------------------------------------------------

    def build_filter_params(
        self, filters: BaseModel | Mapping[str, Any] | None
    ) -> dict[str, str]:
        """Convert filter criteria into query parameters.

        The default dumps pydantic models (excluding ``None`` fields, using
        aliases) and stringifies values. Override for APIs that encode filters
        as a single structured parameter.
        """
        if filters is None:
            return {}
        if isinstance(filters, BaseModel):
            dumped = filters.model_dump(exclude_none=True, by_alias=True)
        else:
            dumped = dict(filters)
        return {
            str(key): value if isinstance(value, str) else str(value)
            for key, value in dumped.items()
        }

    def format_sort(self, sort: str | Sequence[str]) -> dict[str, str]:
        """Convert a sort request into query parameters.

        The default sends ``<sort_param>: <value>``, joining sequences with a
        comma. Override for APIs that split field and direction into separate
        parameters (e.g. ``{"sort": "score", "order": "desc"}``).
        """
        if self.dialect.sort_param is None:
            return {}
        value = sort if isinstance(sort, str) else ",".join(sort)
        return {self.dialect.sort_param: value}

    def build_batch_params(self, field: str, values: Sequence[str]) -> dict[str, Any]:
        """Build the query parameters for one ``batch_get`` chunk.

        The default repeats the key once per value. Override for APIs that
        require an OR-list syntax in a single parameter.
        """
        return {field: list(values)}

    def normalize_id(self, value: str) -> str:
        """Canonicalize an identifier before use in paths, batches, and keys."""
        return value.strip()

    def record_keys(self, entity: E, field: str) -> list[str]:
        """Return every normalized ``field`` value of ``entity``.

        ``batch_get`` keys each entity by whichever of these values was
        requested, so records carrying several ids (for example deduplicated
        records with many DOIs) land under the id the caller asked for.
        Override when the values live somewhere other than ``entity.<field>``.
        """
        value = getattr(entity, field, None)
        if value is None:
            value = getattr(entity, "id", None)
        values = value if isinstance(value, list) else [value]
        return [self.normalize_id(str(item)) for item in values if item is not None]

    def item_path(self, id: str) -> str:
        """Return the single-entity path for ``id``, URL-encoding it."""
        return f"{self.path}/{quote(self.normalize_id(id), safe='')}"

    # --- operations ----------------------------------------------------

    async def get(self, id: str) -> E:
        """Fetch one entity by id; 404 raises :class:`NotFoundError`."""
        response = await self._client.request("GET", self.item_path(id))
        body = response.json()
        data = self._client.unwrapper.item(body)
        return self._validate(data, request=response.request, response=response)

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
    ) -> Page[E]:
        """Fetch one page of results as a typed :class:`Page`.

        ``params`` is the escape hatch for API extras (facets, ``sample``,
        ``seed``); typed wrappers for them belong on client subclasses.
        """
        query_params = self._search_params(
            filters=filters,
            query=query,
            sort=sort,
            select=select,
            page=page,
            page_size=page_size,
            cursor=cursor,
            params=params,
        )
        response = await self._client.request("GET", self.path, params=query_params)
        body = response.json()
        unwrapper = self._client.unwrapper
        results = [
            self._validate(record, request=response.request, response=response)
            for record in unwrapper.results(body)
        ]
        return Page(
            results=results,
            total=unwrapper.total(body),
            next_cursor=unwrapper.next_cursor(body),
            page=page,
            meta=unwrapper.meta(body),
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
    ) -> AsyncIterator[E]:
        """Iterate over all matching entities.

        Uses cursor paging when ``dialect.cursor_param`` is set, otherwise page
        or offset paging. Stops at ``limit``, on an empty page, or when the
        unwrapper reports no next cursor. ``on_page(page_number, next_cursor)``
        checkpoints progress; passing a saved cursor back via ``cursor=``
        resumes a cursor-mode harvest. Records that fail validation raise
        :class:`ValidationError`, or are dropped and recorded in ``failures``
        with ``on_error="skip"``.
        """
        cursor_param = self.dialect.cursor_param
        if cursor_param is not None:
            return self._iterate_cursor(
                cursor_param,
                filters=filters,
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
        return self._iterate_pages(
            filters=filters,
            query=query,
            sort=sort,
            select=select,
            page_size=page_size,
            limit=limit,
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
    ) -> list[E]:
        """Collect ``iterate()`` output into a list, optionally bounded."""
        collected: list[E] = [
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
        return collected

    async def first(
        self,
        filters: BaseModel | Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> E | None:
        """Return the first matching entity, or ``None`` when there is none."""
        results = await self.collect(filters, limit=1, **kwargs)
        return results[0] if results else None

    async def count(
        self,
        filters: BaseModel | Mapping[str, Any] | None = None,
        *,
        query: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> int:
        """Return the total number of matching entities, fetching a minimal page."""
        query_params = self._search_params(
            filters=filters,
            query=query,
            page_size=1,
            cursor=self.dialect.cursor_start,
            params=params,
        )
        response = await self._client.request("GET", self.path, params=query_params)
        return self._client.unwrapper.total(response.json()) or 0

    async def batch_get(
        self,
        ids: Sequence[str],
        *,
        field: str = "id",
        batch_size: int | None = None,
        concurrency: int = 4,
    ) -> dict[str, E]:
        """Fetch entities for many ids in bounded, concurrent chunks.

        Ids are normalized with :meth:`normalize_id` and deduplicated, split
        into chunks of ``batch_size`` (or the class default), fetched
        concurrently under ``concurrency``, and returned keyed by normalized
        id. Missing ids are absent from the result. Each entity is keyed by
        the requested ids found among :meth:`record_keys`.
        """
        size = self.batch_size if batch_size is None else batch_size
        if size <= 0:
            raise ConfigurationError(
                f"{type(self).__name__}.batch_get is disabled (batch_size=0)."
            )
        keys = list(dict.fromkeys(self.normalize_id(value) for value in ids))
        chunks = [keys[start : start + size] for start in range(0, len(keys), size)]
        results: dict[str, E] = {}

        async def fetch_chunk(chunk: list[str]) -> None:
            query_params = self.build_batch_params(field, chunk)
            query_params[self.dialect.page_size_param] = min(
                len(chunk), self.dialect.max_page_size
            )
            response = await self._client.request("GET", self.path, params=query_params)
            requested = set(chunk)
            for record in self._client.unwrapper.results(response.json()):
                entity = self._validate(record, response=response)
                for key in self.record_keys(entity, field):
                    if key in requested:
                        results[key] = entity

        await run_bounded(fetch_chunk, chunks, concurrency)
        return results

    # --- internals -----------------------------------------------------

    def _search_params(
        self,
        *,
        filters: BaseModel | Mapping[str, Any] | None,
        query: str | None = None,
        sort: str | Sequence[str] | None = None,
        select: Sequence[str] | None = None,
        page: int | None = None,
        page_size: int | None = None,
        cursor: str | None = None,
        params: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        dialect = self.dialect
        query_params: dict[str, Any] = dict(self.build_filter_params(filters))
        size = (
            dialect.default_page_size
            if page_size is None
            else min(page_size, dialect.max_page_size)
        )
        query_params[dialect.page_size_param] = size
        if cursor is not None and dialect.cursor_param is not None:
            query_params[dialect.cursor_param] = cursor
        elif dialect.offset_param is not None:
            effective_page = dialect.page_start if page is None else page
            query_params[dialect.offset_param] = (
                effective_page - dialect.page_start
            ) * size
        elif dialect.page_param is not None:
            query_params[dialect.page_param] = (
                dialect.page_start if page is None else page
            )
        if query is not None and dialect.query_param is not None:
            query_params[dialect.query_param] = query
        if select and dialect.select_param is not None:
            query_params[dialect.select_param] = ",".join(select)
        if sort is not None:
            query_params.update(self.format_sort(sort))
        if params is not None:
            query_params.update(params)
        return query_params

    def _validate(
        self,
        data: dict[str, Any],
        *,
        request: Any = None,
        response: Any = None,
    ) -> E:
        try:
            return self.model.model_validate(data)
        except PydanticValidationError as error:
            raise ValidationError(
                f"Failed to validate {self.model.__name__}: {error}",
                raw=data,
                error=error,
                model_name=self.model.__name__,
                request=request,
                response=response,
            ) from error

    def _parse_or_handle(
        self,
        record: dict[str, Any],
        *,
        on_error: OnError,
        failures: list[tuple[dict[str, Any], Exception]] | None,
    ) -> E | None:
        """Validate a record; on failure raise, or skip and record it."""
        try:
            return self.model.model_validate(record)
        except PydanticValidationError as error:
            if on_error == "skip":
                if failures is not None:
                    failures.append((record, error))
                logger.warning(
                    "Skipping record that failed %s validation: %s",
                    self.model.__name__,
                    error,
                )
                return None
            raise ValidationError(
                f"Failed to validate {self.model.__name__}: {error}",
                raw=record,
                error=error,
                model_name=self.model.__name__,
            ) from error

    async def _iterate_cursor(
        self,
        cursor_param: str,
        *,
        filters: BaseModel | Mapping[str, Any] | None,
        query: str | None,
        sort: str | Sequence[str] | None,
        select: Sequence[str] | None,
        page_size: int | None,
        limit: int | None,
        cursor: str | None,
        on_error: OnError,
        failures: list[tuple[dict[str, Any], Exception]] | None,
        on_page: Callable[[int, str | None], Any] | None,
        params: Mapping[str, Any] | None,
    ) -> AsyncIterator[E]:
        dialect = self.dialect
        if page_size is None:
            page_size = dialect.iterate_page_size
        current = cursor if cursor is not None else dialect.cursor_start
        page_number = 0
        fetched = 0
        while True:
            query_params = self._search_params(
                filters=filters,
                query=query,
                sort=sort,
                select=select,
                page=None,
                page_size=page_size,
                cursor=current,
                params=params,
            )
            response = await self._client.request("GET", self.path, params=query_params)
            body = response.json()
            unwrapper = self._client.unwrapper
            results = unwrapper.results(body)
            next_cursor = unwrapper.next_cursor(body)
            if next_cursor == current:  # Solr-style APIs echo the cursor when exhausted
                next_cursor = None
            page_number += 1
            stopped = False
            for record in results:
                entity = self._parse_or_handle(
                    record, on_error=on_error, failures=failures
                )
                if entity is None:
                    continue
                yield entity
                fetched += 1
                if limit is not None and fetched >= limit:
                    stopped = True
                    break
            await _fire_on_page(on_page, page_number, next_cursor)
            if stopped or not results or next_cursor is None:
                return
            current = next_cursor

    async def _iterate_pages(
        self,
        *,
        filters: BaseModel | Mapping[str, Any] | None,
        query: str | None,
        sort: str | Sequence[str] | None,
        select: Sequence[str] | None,
        page_size: int | None,
        limit: int | None,
        on_error: OnError,
        failures: list[tuple[dict[str, Any], Exception]] | None,
        on_page: Callable[[int, str | None], Any] | None,
        params: Mapping[str, Any] | None,
    ) -> AsyncIterator[E]:
        if page_size is None:
            page_size = self.dialect.iterate_page_size
        page = self.dialect.page_start
        fetched = 0
        while True:
            query_params = self._search_params(
                filters=filters,
                query=query,
                sort=sort,
                select=select,
                page=page,
                page_size=page_size,
                params=params,
            )
            response = await self._client.request("GET", self.path, params=query_params)
            body = response.json()
            unwrapper = self._client.unwrapper
            results = unwrapper.results(body)
            total = unwrapper.total(body)
            for record in results:
                entity = self._parse_or_handle(
                    record, on_error=on_error, failures=failures
                )
                if entity is None:
                    continue
                yield entity
                fetched += 1
                if limit is not None and fetched >= limit:
                    return
            await _fire_on_page(on_page, page, None)
            if not results or (total is not None and fetched >= total):
                return
            page += 1
