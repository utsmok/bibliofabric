"""Client for the Semantic Scholar snippet-search route."""

from collections.abc import Sequence
from typing import Any

from bibliofabric import BaseApiClient, validate_model
from bibliofabric.exceptions import ConfigurationError

from ..models import SnippetSearchResult


class SnippetsClient:
    """Client for the ``/snippet/search`` route.

    Snippet search needs an API key with snippet access; keyless
    requests answer HTTP 429 or 403 on the anonymous pool.
    """

    def __init__(self, client: BaseApiClient) -> None:
        self._client = client

    async def search(
        self,
        query: str,
        *,
        fields: Sequence[str] | None = None,
        limit: int | None = None,
    ) -> SnippetSearchResult:
        """Return the snippets that match ``query`` best.

        Each match carries the snippet text, its annotations, a
        ``score``, and a minimal paper record. The default limit is 10
        and the API maximum is 1000.
        """
        text = query.strip()
        if not text:
            raise ConfigurationError("query must be a non-empty string.")
        params: dict[str, Any] = {"query": text}
        if fields:
            params["fields"] = ",".join(fields)
        if limit is not None:
            params["limit"] = limit
        response = await self._client.request("GET", "snippet/search", params=params)
        body = self._client.parse_json(response)
        return validate_model(
            SnippetSearchResult,
            body if isinstance(body, dict) else {},
            request=getattr(response, "request", None),
            response=response,
        )
