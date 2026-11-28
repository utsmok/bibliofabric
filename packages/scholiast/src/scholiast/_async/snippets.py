"""Client for the Semantic Scholar snippet-search route."""

from collections.abc import Mapping, Sequence
from typing import Any

from bibliofabric import BaseApiClient, validate_model
from bibliofabric.exceptions import ConfigurationError

from ..models import SnippetSearchResult


class SnippetsClient:
    """Client for the ``/snippet/search`` route.

    Snippet search needs an API key with snippet access; keyless
    requests answered HTTP 429 on the anonymous pool on 2026-11-27 and
    2026-11-28.
    """

    def __init__(self, client: BaseApiClient) -> None:
        self._client = client

    async def search(
        self,
        query: str,
        *,
        fields: Sequence[str] | None = None,
        limit: int | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> SnippetSearchResult:
        """Return the snippets that match ``query`` best.

        Each match carries the snippet text, its annotations, a
        ``score``, and a minimal paper record. ``fields`` picks parts of
        the snippet, such as ``snippet.text`` or
        ``snippet.annotations.sentences``. The default limit is 10 and
        the API maximum is 1000. ``params`` adds query parameters the
        method does not name, such as ``paperIds``, ``authors``,
        ``year``, or ``venue``.
        """
        text = query.strip()
        if not text:
            raise ConfigurationError("query must be a non-empty string.")
        query_params: dict[str, Any] = {"query": text, **(params or {})}
        if fields:
            query_params["fields"] = ",".join(fields)
        if limit is not None:
            query_params["limit"] = limit
        response = await self._client.request(
            "GET", "snippet/search", params=query_params
        )
        body = self._client.parse_json(response)
        return validate_model(
            SnippetSearchResult,
            body,
            request=getattr(response, "request", None),
            response=response,
        )


__all__ = ["SnippetsClient"]
