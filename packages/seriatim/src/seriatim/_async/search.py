"""Client for the Portal HTML search route (``/search``).

The Portal search answers a server-rendered HTML page for every Accept
header and format parameter (verified 2026-11-27), so this client fetches
the page and parses it with :func:`seriatim.search_parser.parse_search_page`.
"""

from collections.abc import AsyncIterator, Sequence
from typing import Any

import httpx
from bibliofabric import BaseApiClient
from bibliofabric.exceptions import ConfigurationError

from ..dialect import DEFAULT_SEARCH_PAGE_SIZE, PARTNER_REPOSITORIES
from ..models import SearchHit, SearchPage
from ..search_parser import parse_search_page


class SearchClient:
    """Typed client for the Portal free search.

    Reads the HTML result page: the rows of one page come from
    :meth:`page`, the total from the ``data-hits`` value, and
    :meth:`iterate` walks the pages for you. This is an HTML scrape of the
    public search form, not a machine-readable API; the Portal offers no
    JSON variant of ``/search`` (verified 2026-11-27).
    """

    def __init__(self, client: BaseApiClient) -> None:
        """Store the shared :class:`BaseApiClient` (rate limiting, headers)."""
        self._client = client

    async def page(
        self,
        query: str | None = None,
        *,
        fuzzy: bool = False,
        chinese_script: bool = False,
        partner_repositories: Sequence[str] | None = None,
        iso_country: Sequence[str] | None = None,
        media: Sequence[str] | None = None,
        category: Sequence[str] | None = None,
        page: int = 1,
        page_size: int = DEFAULT_SEARCH_PAGE_SIZE,
        sort_field: str | None = None,
        sort_order: str | None = None,
    ) -> SearchPage:
        """Fetch one page of search results.

        The parameters mirror the public search form: ``query`` is the
        ``search`` field; ``fuzzy`` and ``chinese_script`` switch the form's
        checkboxes; ``partner_repositories`` takes ``kee``, ``roa`` or
        ``tra``; ``iso_country`` takes ISO 3166-1 alpha-3 codes;
        ``media`` takes the medium codes shown in the results (``ta`` for
        print, ``cr`` for online); ``category`` takes ``reg`` for confirmed
        records; ``sort_field`` accepts ``search score``, ``title``,
        ``country`` or ``issn`` with ``sort_order`` ``asc`` or ``desc``.
        At least one criterion is required.
        """
        params = self._build_params(
            query,
            fuzzy=fuzzy,
            chinese_script=chinese_script,
            partner_repositories=partner_repositories,
            iso_country=iso_country,
            media=media,
            category=category,
            page=page,
            page_size=page_size,
            sort_field=sort_field,
            sort_order=sort_order,
        )
        if not any(key not in {"page", "page_size"} for key, _ in params):
            raise ConfigurationError("Search requires a query or at least one filter.")
        if page < 1:
            raise ConfigurationError(f"page must be >= 1, got {page}.")
        response = await self._client.request(
            "GET", "search", params=httpx.QueryParams(params)
        )
        return parse_search_page(response.text, page=page, page_size=page_size)

    def iterate(
        self,
        query: str | None = None,
        *,
        fuzzy: bool = False,
        chinese_script: bool = False,
        partner_repositories: Sequence[str] | None = None,
        iso_country: Sequence[str] | None = None,
        media: Sequence[str] | None = None,
        category: Sequence[str] | None = None,
        page_size: int = DEFAULT_SEARCH_PAGE_SIZE,
        sort_field: str | None = None,
        sort_order: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[SearchHit]:
        """Iterate over all hits of the search, page by page.

        Stops at ``limit`` hits, on an empty page, or when ``total`` results
        were seen. Each page costs one paced request.
        """
        return self._iterate(
            query,
            fuzzy=fuzzy,
            chinese_script=chinese_script,
            partner_repositories=partner_repositories,
            iso_country=iso_country,
            media=media,
            category=category,
            page_size=page_size,
            sort_field=sort_field,
            sort_order=sort_order,
            limit=limit,
        )

    async def count(
        self,
        query: str | None = None,
        *,
        fuzzy: bool = False,
        chinese_script: bool = False,
        partner_repositories: Sequence[str] | None = None,
        iso_country: Sequence[str] | None = None,
        media: Sequence[str] | None = None,
        category: Sequence[str] | None = None,
    ) -> int | None:
        """Return the ``data-hits`` total of the search, or ``None`` if absent."""
        result = await self.page(
            query,
            fuzzy=fuzzy,
            chinese_script=chinese_script,
            partner_repositories=partner_repositories,
            iso_country=iso_country,
            media=media,
            category=category,
        )
        return result.total

    @staticmethod
    def _build_params(
        query: str | None,
        *,
        fuzzy: bool,
        chinese_script: bool,
        partner_repositories: Sequence[str] | None,
        iso_country: Sequence[str] | None,
        media: Sequence[str] | None,
        category: Sequence[str] | None,
        page: int,
        page_size: int,
        sort_field: str | None,
        sort_order: str | None,
    ) -> list[tuple[str, Any]]:
        """Build the form parameters; repeated keys repeat the query key."""
        pairs: list[tuple[str, Any]] = []
        if query and query.strip():
            pairs.append(("search", query))
        if fuzzy:
            pairs.append(("fuzzy", "True"))
        if chinese_script:
            pairs.append(("chinese_script", "True"))
        for value in partner_repositories or ():
            if value not in PARTNER_REPOSITORIES:
                raise ConfigurationError(
                    f"partner_repositories accepts {' / '.join(sorted(PARTNER_REPOSITORIES))}, "
                    f"got {value!r}."
                )
            pairs.append(("partner_repositories", value))
        for key, values in (
            ("iso_country", iso_country),
            ("media", media),
            ("category", category),
        ):
            for value in values or ():
                if not value or not value.strip():
                    raise ConfigurationError(f"{key} values must be non-empty.")
                pairs.append((key, value))
        if sort_field is not None:
            pairs.append(("sort_field", sort_field))
        if sort_order is not None:
            pairs.append(("sort_order", sort_order))
        pairs.append(("page", page))
        pairs.append(("page_size", page_size))
        return pairs

    async def _iterate(
        self,
        query: str | None,
        *,
        fuzzy: bool,
        chinese_script: bool,
        partner_repositories: Sequence[str] | None,
        iso_country: Sequence[str] | None,
        media: Sequence[str] | None,
        category: Sequence[str] | None,
        page_size: int,
        sort_field: str | None,
        sort_order: str | None,
        limit: int | None,
    ) -> AsyncIterator[SearchHit]:
        """Fetch page after page until a stop condition holds."""
        seen = 0
        page_number = 1
        while True:
            result = await self.page(
                query,
                fuzzy=fuzzy,
                chinese_script=chinese_script,
                partner_repositories=partner_repositories,
                iso_country=iso_country,
                media=media,
                category=category,
                page=page_number,
                page_size=page_size,
                sort_field=sort_field,
                sort_order=sort_order,
            )
            if not result.hits:
                return
            for hit in result.hits:
                yield hit
                seen += 1
                if limit is not None and seen >= limit:
                    return
            total = result.total
            if total is not None and page_number * page_size >= total:
                return
            page_number += 1


__all__ = ["SearchClient"]
