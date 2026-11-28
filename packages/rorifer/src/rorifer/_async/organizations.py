"""Client for the ROR organizations endpoint."""

from collections.abc import AsyncIterator, Callable, Mapping, Sequence
from typing import Any, override

from bibliofabric import OnError, validate_model
from bibliofabric.exceptions import ConfigurationError
from bibliofabric.paging import Page
from pydantic import BaseModel

from ..crosswalk import fundref_id_from_doi
from ..dialect import ROR_PAGE_SIZE
from ..dump import compact_external_id
from ..filters import external_id_query
from ..models import AffiliationMatch, Organization
from .dialect import RoriferResourceClient

_FUNDREF = "fundref"


def _check_page_size(page_size: int | None) -> None:
    """Raise when a page size is requested; ROR fixes pages at 20 records."""
    if page_size is not None:
        raise ConfigurationError(
            "OrganizationsClient does not support a page size (ROR returns "
            f"{ROR_PAGE_SIZE} records per page); do not pass page_size."
        )


class OrganizationsClient(RoriferResourceClient[Organization]):
    """Client for the ``/organizations`` endpoint.

    Pages hold 20 records and the API serves pages 1 to 500, so one query
    reaches at most 10,000 records. For the whole registry, download a data
    dump through :attr:`RoriferClient.dumps`.
    """

    path = "organizations"
    model = Organization
    batch_size = 0

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
        advanced: str | None = None,
        all_status: bool = False,
    ) -> Page[Organization]:
        """Fetch one page of organizations as a typed :class:`Page`.

        ``query`` is a keyword search over names and external ids;
        ``advanced`` is an Elasticsearch query-string over record fields
        (``query.advanced``, for example ``names.value:"University of
        Twente"``). ROR rejects a request that carries both.
        ``all_status`` includes inactive and withdrawn records; by default
        only active records answer. :attr:`Page.meta` carries ROR's facet
        counts (``types``, ``countries``, ``continents``, ``statuses``) and
        ``time_taken``.

        Raises:
            ConfigurationError: ``page_size``, ``sort``, ``select``, or
                ``cursor`` is set. ROR has no such parameter, so the client
                sends no request.
        """
        _check_page_size(page_size)
        return await super().search(
            filters,
            query=query,
            sort=sort,
            select=select,
            page=page,
            page_size=None,
            cursor=cursor,
            on_error=on_error,
            failures=failures,
            params=self.with_query_options(
                params, advanced=advanced, all_status=all_status
            ),
        )

    @override
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
        advanced: str | None = None,
        all_status: bool = False,
    ) -> AsyncIterator[Organization]:
        """Iterate over all matching organizations, page by page.

        Accepts the same arguments as :meth:`search`. Iteration stops at
        ``limit``, on an empty page, or when ``number_of_results`` records
        were seen. A query with more than 10,000 matches raises
        :class:`~bibliofabric.exceptions.ConfigurationError` when it asks
        for page 501, so pass a ``limit`` of at most 10,000 for broad
        queries.

        Raises:
            ConfigurationError: ``page_size``, ``sort``, ``select``, or
                ``cursor`` is set. ROR has no such parameter, so the client
                sends no request.
        """
        _check_page_size(page_size)
        return super().iterate(
            filters,
            query=query,
            sort=sort,
            select=select,
            page_size=None,
            limit=limit,
            cursor=cursor,
            on_error=on_error,
            failures=failures,
            on_page=on_page,
            params=self.with_query_options(
                params, advanced=advanced, all_status=all_status
            ),
        )

    @override
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
        advanced: str | None = None,
        all_status: bool = False,
    ) -> list[Organization]:
        """Collect the output of :meth:`iterate` into a list, bounded by ``limit``."""
        return [
            organization
            async for organization in self.iterate(
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
                advanced=advanced,
                all_status=all_status,
            )
        ]

    @override
    async def first(
        self,
        filters: BaseModel | Mapping[str, Any] | None = None,
        *,
        query: str | None = None,
        sort: str | Sequence[str] | None = None,
        select: Sequence[str] | None = None,
        page_size: int | None = None,
        cursor: str | None = None,
        on_error: OnError = "raise",
        failures: list[tuple[dict[str, Any], Exception]] | None = None,
        params: Mapping[str, Any] | None = None,
        advanced: str | None = None,
        all_status: bool = False,
    ) -> Organization | None:
        """Return the first matching organization, or ``None`` when there is none.

        ROR fixes pages at 20 records, so the call reads one page and returns
        its first record. It accepts the same arguments as :meth:`iterate`
        except ``limit`` and ``on_page``.
        """
        _check_page_size(page_size)
        results = await self.collect(
            filters,
            limit=1,
            query=query,
            sort=sort,
            select=select,
            page_size=None,
            cursor=cursor,
            on_error=on_error,
            failures=failures,
            params=params,
            advanced=advanced,
            all_status=all_status,
        )
        return results[0] if results else None

    @override
    async def count(
        self,
        filters: BaseModel | Mapping[str, Any] | None = None,
        *,
        query: str | None = None,
        params: Mapping[str, Any] | None = None,
        advanced: str | None = None,
        all_status: bool = False,
    ) -> int:
        """Return ``number_of_results`` of the query.

        ROR has no count-only route, so this fetches one full page.
        """
        return await super().count(
            filters,
            query=query,
            params=self.with_query_options(
                params, advanced=advanced, all_status=all_status
            ),
        )

    async def match_affiliation(self, affiliation: str) -> list[AffiliationMatch]:
        """Match a free-text affiliation string to organizations.

        Runs ROR's affiliation matcher (``?affiliation=``) and returns up to
        10 candidates, each with a ``score`` from 0 to 1; ROR marks one
        candidate ``chosen``. The matched input is in ``substring``.
        """
        text = affiliation.strip()
        if not text:
            raise ConfigurationError("affiliation must be a non-empty string.")
        response = await self._client.request(
            "GET", self.path, params={"affiliation": text}
        )
        body = self._client.parse_json(response)
        return [
            validate_model(
                AffiliationMatch,
                record,
                request=getattr(response, "request", None),
                response=response,
            )
            for record in self._client.unwrapper.results(body)
        ]

    async def find_by_external_id(
        self,
        value: str,
        *,
        id_type: str | None = None,
    ) -> list[Organization]:
        """Return the organizations that carry ``value`` as an external id.

        ``id_type`` restricts the match to one scheme (``fundref``, ``grid``,
        ``isni``, ``wikidata``); ``None`` checks every scheme. ROR matches
        the stored spelling exactly, so an ISNI is searched in its grouped
        and its compact form and a Wikidata id in either case. Inactive and
        withdrawn records are included, because a withdrawn record can
        still be the target of a crosswalk.
        """
        query = external_id_query(value, id_type=id_type)
        matches: list[Organization] = []
        async for organization in self.iterate(advanced=query, all_status=True):
            external_ids = (
                organization.external_ids
                if id_type is None
                else [
                    external_id
                    for external_id in organization.external_ids
                    if external_id.type == id_type
                ]
            )
            if any(
                compact_external_id(candidate) == compact_external_id(value)
                for external_id in external_ids
                for candidate in external_id.all
            ):
                matches.append(organization)
        return matches

    async def find_by_funder_doi(self, doi: str) -> list[Organization]:
        """Return the organizations registered under a Crossref funder DOI.

        ``doi`` is a Crossref Funder Registry DOI such as
        ``10.13039/100000001``; the search uses its FundRef id.
        """
        return await self.find_by_external_id(
            fundref_id_from_doi(doi), id_type=_FUNDREF
        )
