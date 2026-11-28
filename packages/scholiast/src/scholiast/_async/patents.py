"""Client for the Semantic Scholar patent routes."""

from collections.abc import Sequence
from typing import Any

from bibliofabric import BaseApiClient, validate_model
from bibliofabric.exceptions import ConfigurationError
from bibliofabric.paging import Page

from ..models import Patent, PatentCitations
from .resources import fetch_list_page


class PatentsClient:
    """Client for the ``/patent`` routes.

    ``get`` answers keyless; ``search`` and ``outbound_citations`` are
    documented in the API spec and paged like the paper lists.
    """

    def __init__(self, client: BaseApiClient) -> None:
        self._client = client

    async def get(self, ucid: str, *, fields: Sequence[str] | None = None) -> Patent:
        """Return one patent by its UCID (for example ``US10296086B2``)."""
        params: dict[str, Any] | None = {"fields": ",".join(fields)} if fields else None
        response = await self._client.request("GET", f"patent/{ucid}", params=params)
        body = self._client.parse_json(response)
        return validate_model(
            Patent,
            body if isinstance(body, dict) else {},
            request=getattr(response, "request", None),
            response=response,
        )

    async def search(
        self,
        query: str,
        *,
        fields: Sequence[str] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Page[Patent]:
        """Search patents by plain-text query, ranked by BM25 relevance."""
        if not query.strip():
            raise ConfigurationError("query must be a non-empty string.")
        return await fetch_list_page(
            self._client,
            "patent/search",
            Patent,
            fields=fields,
            limit=limit,
            offset=offset,
            query=query,
        )

    async def outbound_citations(
        self,
        paper_id: str,
        *,
        fields: Sequence[str] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> PatentCitations:
        """Return the patents that cite paper ``paper_id``.

        ``paper_id`` takes the paper id forms (``DOI:``, ``CorpusId:``,
        a bare S2 id, and so on).
        """
        params: dict[str, Any] = {}
        if fields:
            params["fields"] = ",".join(fields)
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        response = await self._client.request(
            "GET", f"patent/outbound-citations/{paper_id}", params=params or None
        )
        body = self._client.parse_json(response)
        return validate_model(
            PatentCitations,
            body if isinstance(body, dict) else {},
            request=getattr(response, "request", None),
            response=response,
        )
