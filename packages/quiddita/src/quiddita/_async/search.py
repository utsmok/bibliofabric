"""Client for ``wbsearchentities`` and the REST search routes."""

from collections.abc import Mapping, Sequence
from typing import Any, override

from bibliofabric import OnError
from bibliofabric.exceptions import ConfigurationError
from bibliofabric.paging import Page

from ..dialect import REST_PREFIX
from ..models import EntitySearchResult, RestSearchResult
from .base import WikidataResourceClient


class SearchClient(WikidataResourceClient[EntitySearchResult]):
    """Client for entity and property search.

    ``search()`` uses ``wbsearchentities``; ``search_items()`` and
    ``search_properties()`` use the Wikibase REST API, whose answers carry a
    language-fallback display label. ``wbsearchentities`` reports no total,
    so ``count()`` is not supported; ``iterate()`` walks ``continue`` offset
    pages until the API returns an empty page.
    """

    path = "w/api.php"
    model = EntitySearchResult

    @override
    def default_params(self) -> Mapping[str, Any]:
        return {
            "action": "wbsearchentities",
            "format": "json",
            "language": "en",
            "uselang": "en",
        }

    @override
    async def search(
        self,
        filters: Any = None,
        *,
        query: str | None = None,
        language: str | None = None,
        uselang: str | None = None,
        type: str | None = None,
        strict_language: bool | None = None,
        sort: str | Sequence[str] | None = None,
        select: Sequence[str] | None = None,
        page: int | None = None,
        page_size: int | None = None,
        cursor: str | None = None,
        on_error: OnError = "raise",
        failures: list[tuple[dict[str, Any], Exception]] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Page[EntitySearchResult]:
        """Search entities by label and alias in ``language``.

        Args:
            query: The search text.
            language: Code to search in (default ``en``).
            uselang: Language of the result labels (default ``en``).
            type: ``item``, ``property``, or ``lexeme``.
            strict_language: Search only in ``language``.
            params: Raw ``wbsearchentities`` extras, for example
                ``{"continue": 10}``.
        """
        query_params: dict[str, Any] = {}
        if language is not None:
            query_params["language"] = language
        if uselang is not None:
            query_params["uselang"] = uselang
        if type is not None:
            query_params["type"] = type
        if strict_language is not None:
            query_params["strictlanguage"] = "true" if strict_language else "false"
        if params is not None:
            query_params.update(params)
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
            params=query_params or None,
        )

    @override
    async def count(
        self,
        filters: Any = None,
        *,
        query: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> int:
        """Not supported: ``wbsearchentities`` reports no total."""
        raise ConfigurationError(
            "Wikidata search does not report a total, so count() is not supported."
        )

    async def search_items(
        self,
        query: str,
        *,
        language: str = "en",
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[RestSearchResult]:
        """Search items through the REST route ``/search/items``."""
        return await self._rest_search(
            "search/items", query, language=language, limit=limit, offset=offset
        )

    async def search_properties(
        self,
        query: str,
        *,
        language: str = "en",
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[RestSearchResult]:
        """Search properties through the REST route ``/search/properties``."""
        return await self._rest_search(
            "search/properties", query, language=language, limit=limit, offset=offset
        )

    async def suggest_items(
        self,
        query: str,
        *,
        language: str = "en",
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[RestSearchResult]:
        """Suggest items through the REST route ``/suggest/items``.

        The suggester answers the same result shape as ``/search/items``
        and matches aliases too; its query parameter is ``q`` (verified
        2026-11-28).
        """
        return await self._rest_search(
            "suggest/items", query, language=language, limit=limit, offset=offset
        )

    async def suggest_properties(
        self,
        query: str,
        *,
        language: str = "en",
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[RestSearchResult]:
        """Suggest properties through the REST route ``/suggest/properties``."""
        return await self._rest_search(
            "suggest/properties", query, language=language, limit=limit, offset=offset
        )

    async def _rest_search(
        self,
        kind: str,
        query: str,
        *,
        language: str,
        limit: int | None,
        offset: int | None,
    ) -> list[RestSearchResult]:
        if not query.strip():
            raise ConfigurationError("The search text must be non-empty.")
        request_params: dict[str, Any] = {"q": query, "language": language}
        if limit is not None:
            request_params["limit"] = limit
        if offset is not None:
            request_params["offset"] = offset
        response = await self._client.request(
            "GET", f"{REST_PREFIX}/{kind}", params=request_params
        )
        body = self._client.parse_json(response)
        return [
            RestSearchResult.model_validate(record)
            for record in body.get("results", [])
            if isinstance(record, dict)
        ]


__all__ = ["SearchClient"]
