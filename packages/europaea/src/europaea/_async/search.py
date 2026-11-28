"""Client for the Europe PMC ``/search`` endpoint."""

from collections.abc import AsyncIterator, Callable, Mapping, Sequence
from typing import Any, Literal, override

from bibliofabric import OnError
from bibliofabric.exceptions import ConfigurationError
from bibliofabric.paging import Page
from pydantic import BaseModel

from ..models import FieldsResponse, SearchResult
from .resources import EUROPEPMC_DIALECT, EuropepmcResourceClient

ResultType = Literal["idlist", "lite", "core", "json", "xml", "dc"]
"""The ``resultType`` values of the search route."""

_SORT_FIELDS = (
    "CITED",
    "P_PDATE_D",
    "PDATE",
    "AUTHOR_ID",
    "RELEVANCE",
)


class SearchClient(EuropepmcResourceClient[SearchResult]):
    """Client for the ``/search`` endpoint.

    The route pages with ``cursorMark`` tokens (``ResourceClient.iterate``
    walks them); ``nextCursorMark`` repeats unchanged once the result list is
    exhausted. Records come back in ``resultType=lite`` shape unless the
    caller asks for ``result_type="core"``; the model accepts both.
    """

    path = "search"
    model = SearchResult
    batch_size = 0
    dialect = EUROPEPMC_DIALECT

    @override
    async def search(
        self,
        filters: BaseModel | Mapping[str, Any] | None = None,
        *,
        query: str | None = None,
        sort: str | Sequence[str] | None = None,
        select: Sequence[str] | None = None,
        result_type: ResultType = "core",
        synonym: bool = False,
        page_size: int | None = None,
        page: int | None = None,
        cursor: str | None = None,
        on_error: OnError = "raise",
        failures: list[tuple[dict[str, Any], Exception]] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Page[SearchResult]:
        """Fetch one page of search results as a typed :class:`Page`.

        Args:
            query: Europe PMC query string (for example
                ``"DOI:10.1038/nature12373"`` or ``"cancer AND OPEN_ACCESS:Y"``).
            result_type: ``"lite"`` (metadata scalars) or ``"core"`` (adds
                abstracts, MeSH headings, grants, full text URLs, and more).
            synonym: Expand query terms with MeSH synonyms.
            sort: Sort expression such as ``"CITED desc"`` or
                ``"P_PDATE_D asc"``.

        Returns:
            One page with ``total`` set to ``hitCount`` and ``next_cursor``
            set to ``nextCursorMark``.
        """
        self._check_sort(sort)
        return await super().search(
            filters,
            query=query,
            sort=sort,
            select=select,
            page_size=page_size,
            page=page,
            cursor=cursor,
            on_error=on_error,
            failures=failures,
            params=self._extra_params(result_type, synonym=synonym, params=params),
        )

    @override
    def iterate(
        self,
        filters: BaseModel | Mapping[str, Any] | None = None,
        *,
        query: str | None = None,
        sort: str | Sequence[str] | None = None,
        select: Sequence[str] | None = None,
        result_type: ResultType = "core",
        synonym: bool = False,
        page_size: int | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        on_error: OnError = "raise",
        failures: list[tuple[dict[str, Any], Exception]] | None = None,
        on_page: Callable[[int, str | None], Any] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> AsyncIterator[SearchResult]:
        """Iterate over all matching records, cursor page by cursor page.

        The framework stops when ``nextCursorMark`` repeats, which the API
        does once the result list is exhausted.
        """
        self._check_sort(sort)
        return super().iterate(
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
            params=self._extra_params(result_type, synonym=synonym, params=params),
        )

    async def search_post(
        self,
        filters: BaseModel | Mapping[str, Any] | None = None,
        *,
        query: str | None = None,
        sort: str | Sequence[str] | None = None,
        select: Sequence[str] | None = None,
        result_type: ResultType = "core",
        synonym: bool = False,
        page_size: int | None = None,
        page: int | None = None,
        cursor: str | None = None,
        on_error: OnError = "raise",
        failures: list[tuple[dict[str, Any], Exception]] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Page[SearchResult]:
        """Fetch one page of search results over ``POST /searchPOST``.

        The route is the same search as :meth:`search` with the parameters
        sent as an ``application/x-www-form-urlencoded`` body; the envelope
        and the ``cursorMark`` paging are identical. It is a read-only POST,
        so the request is retried.
        """
        self._check_sort(sort)
        query_params = self._search_params(
            filters=filters,
            query=query,
            sort=sort,
            select=select,
            page=page,
            page_size=page_size,
            cursor=cursor,
            params=self._extra_params(result_type, synonym=synonym, params=params),
        )
        response = await self._client.request(
            "POST",
            "searchPOST",
            data=query_params,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            retry=True,
        )
        body = self._client.parse_json(response)
        unwrapper = self._client.unwrapper
        results = self._validate_records(
            unwrapper.results(body),
            on_error=on_error,
            failures=failures,
            request=SearchClient._response_request(response),
            response=response,
        )
        return Page(
            results=results,
            total=unwrapper.total(body),
            next_cursor=unwrapper.next_cursor(body),
            page=page,
            meta=unwrapper.meta(body),
        )

    def iterate_post(
        self,
        filters: BaseModel | Mapping[str, Any] | None = None,
        *,
        query: str | None = None,
        sort: str | Sequence[str] | None = None,
        select: Sequence[str] | None = None,
        result_type: ResultType = "core",
        synonym: bool = False,
        page_size: int | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        on_error: OnError = "raise",
        failures: list[tuple[dict[str, Any], Exception]] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> AsyncIterator[SearchResult]:
        """Iterate over all matching records over ``POST /searchPOST``.

        The route pages with ``cursorMark`` tokens exactly like the GET
        search; iteration stops when ``nextCursorMark`` repeats.
        """

        async def _generator() -> AsyncIterator[SearchResult]:
            current = cursor if cursor is not None else "*"
            fetched = 0
            while True:
                page = await self.search_post(
                    filters,
                    query=query,
                    sort=sort,
                    select=select,
                    result_type=result_type,
                    synonym=synonym,
                    page_size=page_size,
                    cursor=current,
                    on_error=on_error,
                    failures=failures,
                    params=params,
                )
                for record in page.results:
                    yield record
                    fetched += 1
                    if limit is not None and fetched >= limit:
                        return
                if not page.results or page.next_cursor is None:
                    return
                if page.next_cursor == current:
                    return
                current = page.next_cursor

        return _generator()

    async def fields(self) -> list[str]:
        """Return the searchable index terms of the ``/fields`` endpoint."""
        body = await self._client.get_json("fields", params={"format": "json"})
        document = FieldsResponse.model_validate(body)
        entries = (
            document.search_term_list.search_terms
            if document.search_term_list is not None
            else None
        )
        terms = entries or []
        return [term.term for term in terms if term.term]

    @staticmethod
    def _extra_params(
        result_type: ResultType, *, synonym: bool, params: Mapping[str, Any] | None
    ) -> dict[str, Any]:
        """Merge ``resultType`` and ``synonym`` into the caller parameters."""
        extra: dict[str, Any] = {
            "resultType": result_type,
            "synonym": "true" if synonym else "false",
        }
        if params:
            extra.update(params)
        return extra

    @staticmethod
    def _response_request(response: Any) -> Any:
        """Return the request of a response when the API attaches it."""
        try:
            return response.request
        except RuntimeError:
            return None

    @staticmethod
    def _check_sort(sort: str | Sequence[str] | None) -> None:
        """Reject sort expressions the API would answer with an error page."""
        if sort is None:
            return
        expression = (
            " ".join(sort)
            if isinstance(sort, Sequence) and not isinstance(sort, str)
            else str(sort)
        )
        words = expression.split()
        head = words[0] if words else ""
        if head not in _SORT_FIELDS:
            raise ConfigurationError(
                f"Europe PMC sort must start with one of {_SORT_FIELDS}, "
                f"got {expression!r}."
            )


__all__ = ["ResultType", "SearchClient"]
