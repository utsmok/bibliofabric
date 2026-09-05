"""Generic resource mixins for the bibliofabric framework.

This module provides reusable base classes and mixins that abstract common API
resource operations like getting single entities, searching with pagination, and
cursor-based iteration. These mixins work with the BaseApiClient and
ResponseUnwrapper protocol to provide a consistent interface across different
API implementations.

The mixins are designed to be composable - a concrete resource client can inherit
from multiple mixins as needed to provide the appropriate functionality for that
specific resource type.
"""

import asyncio
import inspect
from collections.abc import AsyncIterator, Callable, Iterator
from typing import TYPE_CHECKING, Any, Literal, Protocol

from pydantic import BaseModel

from .exceptions import BibliofabricError
from .log_config import logger

if TYPE_CHECKING:
    from .client import BaseApiClient
    from .models import ResponseUnwrapper

PagingStrategy = Literal["page", "offset"]
"""Paging style used by ``_paging_params``.

``"page"`` sends ``_param_page``/``_param_page_size`` (OpenAIRE-style), while
``"offset"`` sends ``_param_offset``/``_param_rows`` (Crossref-style), where
page N maps to ``offset=(N-1)*page_size``.
"""

OnError = Literal["raw", "skip", "raise"]
"""Handling for records that fail ``_entity_model`` validation during iteration."""


async def _fire_on_page(
    on_page: Callable[[int, str | None], Any] | None,
    page: int,
    next_cursor: str | None,
) -> None:
    """Invoke an ``on_page`` callback, awaiting its result if it is awaitable.

    Args:
        on_page: The callback (sync or coroutine function), or None.
        page: 1-indexed number of the page that was just fetched and yielded.
        next_cursor: Cursor token for the next page, or None on the final page.
    """
    if on_page is None:
        return
    result = on_page(page, next_cursor)
    if inspect.isawaitable(result):
        await result


class ResourceClientProtocol(Protocol):
    """Protocol that defines the interface expected by resource mixins.

    This protocol ensures that classes using the mixins have the required
    attributes and methods that the mixins depend on.
    """

    _api_client: "BaseApiClient"
    _entity_path: str  # The relative API path for the resource, e.g., "publications"
    _entity_model: type[BaseModel] | None  # Pydantic model for a single entity
    _search_response_model: (
        type[BaseModel] | None
    )  # Pydantic model for the search/list response envelope
    _base_url_override: str | None
    _supports_direct_get: bool
    _paging_strategy: PagingStrategy
    _param_page: str | None
    _param_page_size: str | None
    _param_sort: str | None
    _param_cursor: str | None
    _param_id: str | None
    _param_search: str | None
    _param_offset: str | None
    _param_rows: str | None

    @property
    def response_unwrapper(self) -> "ResponseUnwrapper": ...
    def _validate_sort_field(self, field: str) -> None: ...
    @staticmethod
    def _normalize_sort(sort_by: str) -> str: ...
    def _serialize_filters(
        self, filters: BaseModel | dict[str, Any] | None
    ) -> dict[str, Any]: ...
    def _paging_params(self, page: int, page_size: int) -> dict[str, Any]: ...
    def _iter_parsed(
        self,
        results: list[dict[str, Any]],
        *,
        on_error: OnError,
        failures: list[tuple[dict[str, Any], Exception]] | None,
    ) -> Iterator[Any]: ...


class BaseResourceClient:
    """Base class for all resource clients in the bibliofabric framework.

    This class provides the foundation for resource clients by holding a
    reference to the main API client and providing access to the response
    unwrapper. All resource mixins expect to be used with this base class.

    Attributes:
        _api_client: The main `BaseApiClient` instance used for making HTTP requests.
        _entity_path: The specific API endpoint path for this resource (e.g., "items",
            "users"). This must be defined by concrete subclasses.
        _entity_model: Optional Pydantic model (`type[BaseModel] | None`) that represents
            a single entity of this resource. If provided, methods like `get()`
            and `iterate()` will attempt to parse results into this model.
        _search_response_model: Optional Pydantic model (`type[BaseModel] | None`)
            that represents the structure of a search or list response envelope for
            this resource. If provided, `search()` will attempt to parse the entire
            response into this model.

    Paging is controlled by ``_paging_strategy``: ``"page"`` (default) sends
    ``_param_page``/``_param_page_size`` (e.g. OpenAIRE's ``page``/``pageSize``),
    while ``"offset"`` sends ``_param_offset``/``_param_rows`` (Crossref-style,
    where page N maps to ``offset=(N-1)*page_size``). Any ``_param_*`` attribute
    set to ``None`` omits that query parameter entirely, which lets cursor-only
    clients reuse ``search()`` without sending paging parameters the API would
    reject.
    """

    _base_url_override: str | None = None
    _supports_direct_get: bool = False
    _paging_strategy: PagingStrategy = "page"
    _param_page: str | None = "page"
    _param_page_size: str | None = "pageSize"
    _param_sort: str | None = "sortBy"
    _param_cursor: str | None = "cursor"
    _param_id: str | None = "id"
    _param_search: str | None = "search"
    # Offset ("rows") paging, e.g. Crossref; used when _paging_strategy = "offset".
    _param_offset: str | None = "offset"
    _param_rows: str | None = "rows"

    def __init__(self, api_client: "BaseApiClient"):
        """Initialize the base resource client.

        Args:
            api_client: An instance of BaseApiClient for making HTTP requests.
        """
        self._api_client = api_client
        logger.debug(f"{self.__class__.__name__} initialized")

    @property
    def response_unwrapper(self) -> "ResponseUnwrapper":
        """Get the response unwrapper from the API client.

        Returns:
            ResponseUnwrapper: The response unwrapper instance from the API client.
        """
        return self._api_client._response_unwrapper

    def _validate_sort_field(self, field: str) -> None:
        """Validate a sort field name. Override in subclasses for custom validation.

        Default implementation does nothing (no validation).
        Consumers can override to check against allowed fields.

        Args:
            field: The sort field name to validate.

        Raises:
            ValidationError: If the sort field is invalid.
        """
        ...  # noqa: PIE790

    @staticmethod
    def _normalize_sort(sort_by: str) -> str:
        """Normalize sort expression to use uppercase direction.

        Some APIs (e.g. OpenAIRE Graph v2) require the direction keyword
        in uppercase (``DESC`` / ``ASC``). This helper ensures consistent
        casing regardless of what the caller passes.

        Args:
            sort_by: Sort expression like ``"publicationDate desc"``.

        Returns:
            Normalized expression like ``"publicationDate DESC"``.
        """
        parts = sort_by.strip().split()
        if len(parts) == 2:  # noqa: PLR2004
            return f"{parts[0]} {parts[1].upper()}"
        return sort_by

    def _serialize_filters(
        self, filters: BaseModel | dict[str, Any] | None
    ) -> dict[str, Any]:
        if filters is None:
            return {}
        if isinstance(filters, BaseModel):
            return filters.model_dump(exclude_none=True, by_alias=True)
        if isinstance(filters, dict):
            return dict(filters)
        raise BibliofabricError(
            f"filters must be a Pydantic model or dictionary, got {type(filters)}"
        )

    def _paging_params(self, page: int, page_size: int) -> dict[str, Any]:
        """Translate a logical (page, page_size) pair into query parameters.

        The translation follows ``_paging_strategy``:

        - ``"page"``: sends ``_param_page`` and ``_param_page_size`` (e.g.
          OpenAIRE's ``page``/``pageSize``).
        - ``"offset"``: Crossref-style paging, where page N becomes
          ``offset=(N-1)*page_size`` sent as ``_param_offset`` and the page
          size as ``_param_rows``.

        Any parameter whose ``_param_*`` name is ``None`` is omitted entirely.

        Args:
            page: 1-indexed page number.
            page_size: Number of results per page.

        Returns:
            Query parameters expressing the requested page.
        """
        params: dict[str, Any] = {}
        if self._paging_strategy == "offset":
            if self._param_offset is not None:
                params[self._param_offset] = (page - 1) * page_size
            if self._param_rows is not None:
                params[self._param_rows] = page_size
            return params
        if self._param_page is not None:
            params[self._param_page] = page
        if self._param_page_size is not None:
            params[self._param_page_size] = page_size
        return params

    def _iter_parsed(
        self: ResourceClientProtocol,
        results: list[dict[str, Any]],
        *,
        on_error: OnError = "raw",
        failures: list[tuple[dict[str, Any], Exception]] | None = None,
    ) -> Iterator[Any]:
        """Parse raw records with ``_entity_model``, applying the failure policy.

        Args:
            results: Raw record dictionaries from a single page.
            on_error: Handling for records that fail validation. ``"raw"``
                (default) logs a warning and yields the raw dictionary,
                ``"skip"`` logs a warning and drops the record (appending
                ``(raw_dict, exception)`` to ``failures`` when provided), and
                ``"raise"`` lets the validation error propagate.
            failures: Caller-owned list that collects ``(raw_dict, exception)``
                pairs for skipped records when ``on_error="skip"``.

        Yields:
            Parsed entity models (or raw dictionaries when ``_entity_model``
            is None).
        """
        for result_data in results:
            if self._entity_model is None:
                yield result_data
                continue
            try:
                yield self._entity_model.model_validate(result_data)
            except Exception as e:
                if on_error == "raise":
                    raise
                if on_error == "skip":
                    logger.warning(
                        f"Failed to parse entity data with {self._entity_model.__name__}: {e}. "
                        "Skipping record."
                    )
                    if failures is not None:
                        failures.append((result_data, e))
                    continue
                logger.warning(
                    f"Failed to parse entity data with {self._entity_model.__name__}: {e}. "
                    "Yielding raw data."
                )
                yield result_data

    async def collect(
        self,
        *,
        filters: BaseModel | dict[str, Any] | None = None,
        limit: int | None = None,
        sort_by: str | None = None,
        page_size: int = 100,
        search: str | None = None,
    ) -> list[Any]:
        """Collect results into a list, optionally limited.

        Uses the subclass's ``iterate()`` method if available, otherwise falls back
        to a single ``search()`` call.

        Args:
            filters: Filter criteria.
            limit: Maximum number of results to collect. None = collect all.
            sort_by: Field to sort by.
            page_size: Number of results per page during iteration.

        Returns:
            A list of entities (parsed models if ``_entity_model`` is set).
        """
        collected: list[Any] = []
        iterate_kwargs: dict[str, Any] = {
            "page_size": page_size,
            "sort_by": sort_by,
            "filters": filters,
        }
        if search is not None:
            iterate_kwargs["search"] = search
        # Prefer iterate (handles all pagination types) if the subclass has it
        if hasattr(self, "iterate"):
            async for entity in self.iterate(  # ty: ignore[call-non-callable]
                **iterate_kwargs
            ):
                collected.append(entity)
                if limit is not None and len(collected) >= limit:
                    break
        elif hasattr(self, "search"):
            # Fallback: single page search
            search_kwargs: dict[str, Any] = {
                "page": 1,
                "page_size": min(limit or page_size, page_size),
                "sort_by": sort_by,
                "filters": filters,
            }
            if search is not None:
                search_kwargs["search"] = search
            response = await self.search(  # ty: ignore[call-non-callable]
                **search_kwargs
            )
            if isinstance(response, BaseModel):
                results = getattr(response, "results", None)
                if results:
                    collected = list(results)[:limit] if limit else list(results)
            elif isinstance(response, dict):
                collected = (
                    response.get("results", [])[:limit]
                    if limit
                    else response.get("results", [])
                )
        return collected

    async def count(
        self,
        *,
        filters: BaseModel | dict[str, Any] | None = None,
        search: str | None = None,
    ) -> int:
        """Return total number of matching entities without fetching all results.

        Performs a minimal search (page_size=1) and reads the total from
        the response header.

        Args:
            filters: Filter criteria.

        Returns:
            Total count of matching entities, or 0 if unavailable.
        """
        if not hasattr(self, "search"):
            raise NotImplementedError(
                f"{self.__class__.__name__} does not support search; count() unavailable"
            )
        response = await self.search(
            page=1, page_size=1, filters=filters, search=search
        )  # ty: ignore[call-non-callable]
        if isinstance(response, BaseModel):
            header = getattr(response, "header", None)
            if header and hasattr(header, "numFound") and header.numFound is not None:
                return header.numFound
        elif isinstance(response, dict):
            header = response.get("header", {})
            total = header.get("numFound")
            if total is not None:
                return int(total)
        return 0

    async def first(
        self,
        *,
        filters: BaseModel | dict[str, Any] | None = None,
        sort_by: str | None = None,
        search: str | None = None,
    ) -> Any | None:
        """Return the first matching entity, or None if no results.

        Args:
            filters: Filter criteria.
            sort_by: Field to sort by.
            search: Free-text search query.

        Returns:
            The first entity, or None.
        """
        results = await self.collect(
            filters=filters, limit=1, sort_by=sort_by, page_size=1, search=search
        )
        return results[0] if results else None


class GettableMixin:
    """Mixin that provides generic get() functionality for retrieving single entities.

    This mixin implements a standard pattern for fetching individual entities by ID.
    It typically uses a search operation filtered by the entity's ID, as some APIs
    may not offer direct GET-by-ID endpoints, or this approach offers more
    consistency.

    To use this mixin, a class must:
    1. Inherit from `BaseResourceClient` (or a class that provides the
       `ResourceClientProtocol` attributes).
    2. Define `_entity_path: str` specifying the API endpoint path for the resource.
    3. Optionally, define `_entity_model: type[BaseModel] | None`. If provided,
       the retrieved entity data will be parsed into an instance of this model.
       If None, raw dictionary data is returned.
    """

    async def get(self: ResourceClientProtocol, entity_id: str) -> Any:
        """Retrieve a single entity by its ID.

        This method performs a search operation with the entity ID to fetch
        a single entity. It uses the response unwrapper to extract the entity
        data from the API response.

        Args:
            entity_id: The unique identifier of the entity to retrieve.

        Returns:
            Any: The entity data, either as a parsed Pydantic model (if _entity_model
                is defined) or as a raw dictionary.

        Raises:
            BibliofabricError: If the entity is not found or if the API request fails.
        """
        if not self._entity_path:
            raise BibliofabricError(
                f"{self.__class__.__name__} must define _entity_path"
            )

        logger.debug(f"Fetching entity with ID: {entity_id}")

        try:
            if self._supports_direct_get:
                # Direct GET by ID: construct path like "resource/{id}"
                direct_path = f"{self._entity_path}/{entity_id}"
                response = await self._api_client.request(
                    "GET",
                    direct_path,
                    params=None,
                    base_url_override=self._base_url_override,
                )
                response_data = response.json()
                entity_data = self.response_unwrapper.unwrap_single_item(response_data)
            else:
                # Use search with ID parameter instead of direct GET
                params: dict[str, Any] = {}
                if self._param_id is not None:
                    params[self._param_id] = entity_id
                if self._param_page_size is not None:
                    params[self._param_page_size] = 1
                response = await self._api_client.request(
                    "GET",
                    self._entity_path,
                    params=params,
                    base_url_override=self._base_url_override,
                )
                response_data = response.json()
                # Use the response unwrapper to get results
                results = self.response_unwrapper.unwrap_results(response_data)
                if not results:
                    entity_name = (
                        self._entity_model.__name__ if self._entity_model else "Entity"
                    )
                    raise BibliofabricError(
                        f"{entity_name} with ID '{entity_id}' not found."
                    )
                # Get the first (and should be only) result
                entity_data = results[0]
            # Parse with entity model if available
            if self._entity_model:
                try:
                    return self._entity_model.model_validate(entity_data)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse entity data with {self._entity_model.__name__}: {e}. "
                        "Returning raw data."
                    )
                    return entity_data
            return entity_data

        except Exception as e:
            if isinstance(e, BibliofabricError):
                raise
            logger.exception(
                f"Failed to fetch entity {entity_id} from {self._entity_path}"
            )
            raise BibliofabricError(
                f"Unexpected error fetching entity {entity_id}: {e}"
            ) from e


class SearchableMixin:
    """Mixin that provides generic search() functionality with pagination support.

    This mixin implements a standard pattern for searching entities with support
    for pagination (page-based, or Crossref-style offset/rows when
    ``_paging_strategy = "offset"``), filtering, and sorting. It relies on the
    `ResponseUnwrapper` (via `BaseResourceClient`) to correctly parse the
    API's specific list response structure.

    To use this mixin, a class must:
    1. Inherit from `BaseResourceClient` (or a class that provides the
       `ResourceClientProtocol` attributes).
    2. Define `_entity_path: str` specifying the API endpoint path for the resource.
    3. Optionally, define `_search_response_model: type[BaseModel] | None`.
       If provided, the entire search response (including pagination details and
       results) will be parsed into an instance of this model. If None, the raw
       JSON response dictionary is returned.
    4. Optionally, override `_validate_sort_field()` in your resource client
       if you want to validate the `sort_by` parameter against allowed fields.
    """

    async def search(
        self: ResourceClientProtocol,
        page: int = 1,
        page_size: int = 20,
        sort_by: str | None = None,
        filters: BaseModel | dict[str, Any] | None = None,
        search: str | None = None,
    ) -> BaseModel | dict[str, Any]:
        """Search for entities with pagination support.

        Args:
            page: Page number (1-indexed). With ``_paging_strategy = "offset"``
                (Crossref-style APIs) this is translated to
                ``offset=(page-1)*page_size`` sent as ``_param_offset``, with
                the size sent as ``_param_rows``.
            page_size: Number of results per page.
            sort_by: Field to sort by (e.g., 'title asc', 'date desc').
            filters: Filter criteria as a Pydantic model or dictionary.

        Returns:
            Any: Search results, either as a parsed Pydantic model (if
                _search_response_model is defined) or as raw response data.

        Raises:
            BibliofabricError: If the API request fails.
        """

        if not self._entity_path:
            raise BibliofabricError(
                f"{self.__class__.__name__} must define _entity_path"
            )

        # Build query parameters (paging params follow _paging_strategy and any
        # parameter whose _param_* name is None is omitted entirely)
        params = self._serialize_filters(filters)
        params.update(self._paging_params(page, page_size))
        if sort_by:
            self._validate_sort_field(sort_by.split()[0])
            if self._param_sort is not None:
                params[self._param_sort] = self._normalize_sort(sort_by)
        if search is not None and self._param_search:
            params[self._param_search] = search
        logger.debug(
            f"Searching {self._entity_path}: page={page}, size={page_size}, "
            f"sort='{sort_by}', filters={params}"
        )
        try:
            response = await self._api_client.request(
                "GET",
                self._entity_path,
                params=params,
                base_url_override=self._base_url_override,
            )

            response_data = response.json()

            # Parse with search response model if available
            if self._search_response_model:
                try:
                    return self._search_response_model.model_validate(response_data)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse search response with {self._search_response_model.__name__}: {e}. "
                        "Returning raw data."
                    )
                    return response_data

            return response_data

        except Exception as e:
            if isinstance(e, BibliofabricError):
                raise
            logger.exception(
                f"Failed to search {self._entity_path} with params {params}"
            )
            raise BibliofabricError(
                f"Unexpected error searching {self._entity_path}: {e}"
            ) from e


class CursorIterableMixin:
    """Mixin that provides generic iterate() functionality using cursor-based pagination.

    This mixin implements a standard pattern for iterating through all results
    of a resource using cursor-based pagination. It automatically handles fetching
    subsequent pages by using the `nextCursor` (or equivalent) provided by the API,
    as interpreted by the `ResponseUnwrapper`. It yields individual entities.

    To use this mixin, a class must:
    1. Inherit from `BaseResourceClient` (or a class that provides the
       `ResourceClientProtocol` attributes, including access to a `ResponseUnwrapper`).
    2. Define `_entity_path: str` specifying the API endpoint path for the resource.
    3. Optionally, define `_entity_model: type[BaseModel] | None`. If provided,
       each yielded entity will be parsed into an instance of this model.
       If None, raw dictionary data for each entity is yielded.
    """

    async def iterate(
        self: ResourceClientProtocol,
        page_size: int = 100,
        sort_by: str | None = None,
        filters: BaseModel | dict[str, Any] | None = None,
        search: str | None = None,
        *,
        cursor: str | None = None,
        on_error: OnError = "raw",
        failures: list[tuple[dict[str, Any], Exception]] | None = None,
        on_page: Callable[[int, str | None], Any] | None = None,
    ) -> AsyncIterator[Any]:
        """Iterate through all entities matching the criteria using cursor pagination.

        This method automatically handles pagination by using cursors to fetch
        successive pages of results. It yields individual entities as they are
        retrieved from each page.

        Args:
            page_size: Number of results to fetch per API call during iteration.
            sort_by: Field to sort by.
            filters: Filter criteria as a Pydantic model or dictionary.
            cursor: Cursor token to resume iteration from, e.g. the last cursor
                reported via ``on_page`` by an interrupted harvest. None starts
                from the beginning (``"*"``).
            on_error: Handling for records that fail ``_entity_model``
                validation. ``"raw"`` (default) logs a warning and yields the
                raw dictionary, ``"skip"`` logs a warning and drops the record
                (appending ``(raw_dict, exception)`` to ``failures`` when
                provided), and ``"raise"`` lets the validation error propagate
                (wrapped into ``BibliofabricError`` by the outer error handler).
            failures: Caller-owned list collecting ``(raw_dict, exception)``
                pairs for skipped records when ``on_error="skip"``.
            on_page: Optional callback invoked after each page is fetched and
                yielded, as ``(page_number, next_cursor)`` where ``next_cursor``
                is the cursor of the next page, or None on the final page. May
                be a coroutine function. Use it to checkpoint harvests, and
                pass a saved cursor back in via ``cursor=`` to resume.

        Yields:
            Any: Individual entities, either as parsed Pydantic models (if
                _entity_model is defined) or as raw dictionaries.

        Raises:
            BibliofabricError: If the API request fails during iteration.
        """
        if not self._entity_path:
            raise BibliofabricError(
                f"{self.__class__.__name__} must define _entity_path"
            )

        # Convert filters to dictionary if it's a Pydantic model
        filter_dict = self._serialize_filters(filters)
        logger.debug(
            f"Iterating {self._entity_path}: pageSize={page_size}, "
            f"sort='{sort_by}', filters={filter_dict}"
        )
        # Build initial parameters with cursor pagination; parameters whose
        # _param_* name is None are omitted entirely.
        current_params: dict[str, Any] = {}
        if self._param_cursor is not None:
            current_params[self._param_cursor] = cursor if cursor is not None else "*"
        if self._param_page_size is not None:
            current_params[self._param_page_size] = page_size

        if sort_by and self._param_sort is not None:
            current_params[self._param_sort] = self._normalize_sort(sort_by)

        if filter_dict:
            current_params.update(filter_dict)
        if search is not None and self._param_search:
            current_params[self._param_search] = search

        page_count = 0
        while True:
            try:
                logger.debug(
                    f"Iterating {self._entity_path} with params: {current_params}"
                )

                # Pass a copy of params to avoid issues with mock call_args_list
                response = await self._api_client.request(
                    "GET",
                    self._entity_path,
                    params=current_params.copy(),
                    base_url_override=self._base_url_override,
                )

                response_data = response.json()

                # Use the response unwrapper to get results and next cursor
                results = self.response_unwrapper.unwrap_results(response_data)
                next_cursor = self.response_unwrapper.get_next_page_token(response_data)
                page_count += 1

                if not results:
                    logger.debug(
                        f"No more results for {self._entity_path}, stopping iteration."
                    )
                    await _fire_on_page(on_page, page_count, None)
                    break

                # Yield each parsed result
                for entity in self._iter_parsed(
                    results, on_error=on_error, failures=failures
                ):
                    yield entity

                # Check if there are more pages
                if not next_cursor:
                    logger.debug(
                        f"No nextCursor for {self._entity_path}, stopping iteration."
                    )
                    await _fire_on_page(on_page, page_count, None)
                    break

                # Report the cursor that continues this iteration (checkpoint hook)
                await _fire_on_page(on_page, page_count, next_cursor)

                # Update cursor for next iteration
                if self._param_cursor is not None:
                    current_params[self._param_cursor] = next_cursor
                # Remove page if it accidentally got in, cursor handles pagination
                if self._param_page is not None:
                    current_params.pop(self._param_page, None)

            except Exception as e:
                if isinstance(e, BibliofabricError):
                    raise
                logger.exception(
                    f"Failed during iteration of {self._entity_path} with params {current_params}"
                )
                raise BibliofabricError(
                    f"Unexpected error during iteration of {self._entity_path}: {e}"
                ) from e


class PageIterableMixin:
    """Mixin that provides generic iterate() functionality using page-based pagination.

    This mixin implements a standard pattern for iterating through all results
    of a resource using page-based pagination (incrementing page numbers, or
    Crossref-style offset/rows when ``_paging_strategy = "offset"``).
    It yields individual entities.

    To use this mixin, a class must:
    1. Inherit from `BaseResourceClient` (or provide the ResourceClientProtocol attributes).
    2. Define `_entity_path: str` specifying the API endpoint path for the resource.
    3. Optionally, define `_entity_model: type[BaseModel] | None` for per-entity parsing.
    """

    async def iterate(
        self: ResourceClientProtocol,
        page_size: int = 100,
        sort_by: str | None = None,
        filters: BaseModel | dict[str, Any] | None = None,
        search: str | None = None,
        *,
        on_error: OnError = "raw",
        failures: list[tuple[dict[str, Any], Exception]] | None = None,
        on_page: Callable[[int, str | None], Any] | None = None,
        concurrency: int = 1,
    ) -> AsyncIterator[Any]:
        """Iterate through all entities matching the criteria using page-based pagination.

        This method automatically handles pagination by incrementing the page number
        (or the offset, for ``_paging_strategy = "offset"``) to fetch successive
        pages of results. It yields individual entities.

        Args:
            page_size: Number of results to fetch per API call during iteration.
            sort_by: Field to sort by.
            filters: Filter criteria as a Pydantic model or dictionary.
            on_error: Handling for records that fail ``_entity_model``
                validation. ``"raw"`` (default) logs a warning and yields the
                raw dictionary, ``"skip"`` logs a warning and drops the record
                (appending ``(raw_dict, exception)`` to ``failures`` when
                provided), and ``"raise"`` lets the validation error propagate
                (wrapped into ``BibliofabricError`` by the error handler).
            failures: Caller-owned list collecting ``(raw_dict, exception)``
                pairs for skipped records when ``on_error="skip"``.
            on_page: Optional callback invoked after each page is fetched and
                yielded, as ``(page_number, None)`` — page-based paging has no
                cursor token, so the page number is the checkpoint. May be a
                coroutine function.
            concurrency: Maximum number of page requests in flight at once
                (default 1 = sequential). When greater than 1 and the total
                result count is known (reported by the response unwrapper),
                remaining pages are fetched in bounded chunks of
                ``concurrency`` via ``asyncio.gather`` while results are still
                yielded in page order, stopping at
                ``ceil(total / page_size)`` pages. Falls back to sequential
                iteration when the total is unknown.

        Yields:
            Any: Individual entities, either as parsed Pydantic models (if
                _entity_model is defined) or as raw dictionaries.

        Raises:
            BibliofabricError: If the API request fails during iteration.
        """
        if not self._entity_path:
            raise BibliofabricError(
                f"{self.__class__.__name__} must define _entity_path"
            )

        # Convert filters to dictionary if it's a Pydantic model
        base_params = self._serialize_filters(filters)
        if sort_by:
            self._validate_sort_field(sort_by.split()[0])
            if self._param_sort is not None:
                base_params[self._param_sort] = self._normalize_sort(sort_by)
        if search is not None and self._param_search:
            base_params[self._param_search] = search

        logger.debug(
            f"Iterating {self._entity_path} (page-based): pageSize={page_size}, "
            f"sort='{sort_by}', filters={base_params}"
        )

        async def fetch_page(page: int) -> tuple[list[Any], int | None, bool]:
            """Fetch one page, returning (parsed entities, total, has_results)."""
            page_params = {**base_params, **self._paging_params(page, page_size)}
            try:
                response = await self._api_client.request(
                    "GET",
                    self._entity_path,
                    params=page_params,
                    base_url_override=self._base_url_override,
                )

                response_data = response.json()

                # Use the response unwrapper to get results
                results = self.response_unwrapper.unwrap_results(response_data)
                entities = list(
                    self._iter_parsed(results, on_error=on_error, failures=failures)
                )
                total = self.response_unwrapper.get_total_results(response_data)
                return entities, total, bool(results)
            except Exception as e:
                if isinstance(e, BibliofabricError):
                    raise
                logger.exception(
                    f"Failed during iteration of {self._entity_path} with params {page_params}"
                )
                raise BibliofabricError(
                    f"Unexpected error during iteration of {self._entity_path}: {e}"
                ) from e

        current_page = 1

        while True:
            entities, total, has_results = await fetch_page(current_page)

            if has_results:
                for entity in entities:
                    yield entity

            await _fire_on_page(on_page, current_page, None)

            if not has_results:
                logger.debug(
                    f"No more results for {self._entity_path} at page {current_page}, stopping iteration."
                )
                break

            if total is not None and current_page * page_size >= total:
                logger.debug(
                    f"Fetched all {total} results for {self._entity_path}, stopping iteration."
                )
                break

            if concurrency > 1 and total is not None:
                # Total is known, so the remaining page numbers are computable:
                # fetch them in bounded chunks while still yielding in order.
                last_page = -(-total // page_size)  # ceil(total / page_size)
                page_no = current_page + 1
                while page_no <= last_page:
                    chunk = range(page_no, min(page_no + concurrency, last_page + 1))
                    pages = await asyncio.gather(*(fetch_page(p) for p in chunk))
                    exhausted = False
                    for page, (page_entities, _, page_has_results) in zip(
                        chunk, pages, strict=True
                    ):
                        if page_has_results:
                            for entity in page_entities:
                                yield entity
                        await _fire_on_page(on_page, page, None)
                        if not page_has_results:
                            exhausted = True
                    if exhausted:
                        logger.debug(
                            f"No more results for {self._entity_path} at page {page}, stopping iteration."
                        )
                        break
                    page_no = chunk[-1] + 1
                break

            current_page += 1
