"""Client for the Semantic Scholar patent routes."""

from collections.abc import Sequence
from typing import Any

from bibliofabric import BaseApiClient, validate_model
from bibliofabric.exceptions import ConfigurationError
from bibliofabric.paging import Page

from ..models import Patent, PatentCitations
from .resources import fetch_list_page, id_path


class PatentsClient:
    """Client for the ``/patent`` routes.

    All three routes answered without an API key on 2026-11-28.
    ``search`` and ``outbound_citations`` are paged like the paper
    lists.
    """

    def __init__(self, client: BaseApiClient) -> None:
        self._client = client

    async def get(self, ucid: str, *, fields: Sequence[str] | None = None) -> Patent:
        """Return one patent by its UCID (for example ``US10296086B2``).

        Without ``fields`` the answer holds ``ucid`` and ``title``; ask
        for ``abstract``, ``claims``, ``inventors``, and the other names
        of the ``Patent`` model for the full record. ``claims`` is
        served by this route only.
        """
        params: dict[str, Any] | None = {"fields": ",".join(fields)} if fields else None
        response = await self._client.request(
            "GET", f"patent/{id_path(ucid)}", params=params
        )
        body = self._client.parse_json(response)
        return validate_model(
            Patent,
            body,
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
        """Search patents by plain-text query, ranked by BM25 relevance.

        The answer holds ``ucid`` and ``title`` only unless ``fields``
        names more. A page holds at most 100 patents, and ``claims`` is
        not served here: ask :meth:`get` for it.
        """
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
        a bare S2 id, and so on). A paper that no patent cites answers
        HTTP 404, which raises :class:`NotFoundError`. ``claims`` is not
        served here.
        """
        params: dict[str, Any] = {}
        if fields:
            params["fields"] = ",".join(fields)
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        response = await self._client.request(
            "GET",
            f"patent/outbound-citations/{id_path(paper_id)}",
            params=params or None,
        )
        body = self._client.parse_json(response)
        return validate_model(
            PatentCitations,
            body,
            request=getattr(response, "request", None),
            response=response,
        )


__all__ = ["PatentsClient"]
