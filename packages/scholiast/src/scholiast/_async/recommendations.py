"""Client for the Semantic Scholar Recommendations API."""

from collections.abc import Mapping, Sequence
from typing import Any

from bibliofabric import BaseApiClient, validate_model
from bibliofabric.exceptions import ConfigurationError

from ..dialect import SEMANTICSCHOLAR_RECOMMENDATIONS_BASE_URL
from ..models import Paper
from .resources import id_path


class RecommendationsClient:
    """Client for the ``/recommendations/v1`` routes.

    Both routes answer ``{"recommendedPapers": [...]}`` and work without an
    API key; ``for_list`` is more restricted upstream and may answer 400 on
    the anonymous pool.
    """

    def __init__(self, client: BaseApiClient) -> None:
        self._client = client

    async def for_paper(
        self,
        id: str,
        *,
        fields: Sequence[str] | None = None,
        limit: int | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> list[Paper]:
        """Return papers related to ``id`` (``GET /papers/forpaper/{id}``).

        ``id`` takes the same forms as a paper get (``DOI:``,
        ``ARXIV:``, a bare S2 id, and so on). ``params`` adds query
        parameters the method does not name, such as ``from``
        (``recent``, the default, or ``all-cs``).
        """
        query_params: dict[str, Any] = dict(params or {})
        if fields:
            query_params["fields"] = ",".join(fields)
        if limit is not None:
            query_params["limit"] = limit
        response = await self._client.request(
            "GET",
            f"{SEMANTICSCHOLAR_RECOMMENDATIONS_BASE_URL}/papers/forpaper/{id_path(id)}",
            params=query_params or None,
        )
        body = self._client.parse_json(response)
        return self._parse(response, body)

    async def for_list(
        self,
        positive_paper_ids: Sequence[str],
        negative_paper_ids: Sequence[str] = (),
        *,
        fields: Sequence[str] | None = None,
        limit: int | None = None,
    ) -> list[Paper]:
        """Return recommendations for a list of papers (``POST /papers/``).

        ``positive_paper_ids`` steers toward these papers;
        ``negative_paper_ids`` steers away. Both take the same id forms
        as a paper get. The POST is read-only and is sent with retries.
        """
        if not positive_paper_ids and not negative_paper_ids:
            raise ConfigurationError(
                "at least one positive or negative paper id is required."
            )
        params: dict[str, Any] = {}
        if fields:
            params["fields"] = ",".join(fields)
        if limit is not None:
            params["limit"] = limit
        response = await self._client.request(
            "POST",
            f"{SEMANTICSCHOLAR_RECOMMENDATIONS_BASE_URL}/papers/",
            params=params or None,
            json={
                "positivePaperIds": list(positive_paper_ids),
                "negativePaperIds": list(negative_paper_ids),
            },
            retry=True,
        )
        body = self._client.parse_json(response)
        return self._parse(response, body)

    def _parse(self, response: Any, body: Any) -> list[Paper]:
        papers = body.get("recommendedPapers") if isinstance(body, dict) else None
        if not isinstance(papers, list):
            return []
        return [
            validate_model(
                Paper,
                record,
                request=getattr(response, "request", None),
                response=response,
            )
            for record in papers
            if record is not None
        ]


__all__ = ["RecommendationsClient"]
