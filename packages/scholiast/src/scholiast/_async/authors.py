"""Client for the Semantic Scholar author endpoints."""

from collections.abc import Sequence
from typing import Any, override

from bibliofabric import validate_model
from bibliofabric.exceptions import ConfigurationError
from bibliofabric.paging import Page

from ..dialect import AUTHOR_BATCH_MAX_IDS
from ..models import Author, Paper
from .resources import ScholiastResourceClient, fetch_list_page


class AuthorsClient(ScholiastResourceClient[Author]):
    """Client for the ``/author`` routes.

    ``get``, ``search``, ``iterate``, ``collect``, ``first``, ``count``,
    and ``exists`` come from the resource base; ``fields`` is the
    ``select`` argument everywhere.
    """

    path = "author"
    model = Author
    batch_size = AUTHOR_BATCH_MAX_IDS

    @override
    def search_path(self, query: str | None) -> str:
        """Return ``author/search``; the query always travels on the search route."""
        return "author/search"

    async def papers(
        self,
        id: str,
        *,
        fields: Sequence[str] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Page[Paper]:
        """Fetch one page of the papers written by author ``id``.

        The route serves at most the most recent 10,000 papers.
        ``page.next_cursor`` is the next offset, or ``None`` on the last
        page.
        """
        return await fetch_list_page(
            self._client,
            f"author/{id}/papers",
            Paper,
            fields=fields,
            limit=limit,
            offset=offset,
        )

    async def batch(
        self,
        ids: Sequence[str],
        *,
        fields: Sequence[str] | None = None,
    ) -> list[Author]:
        """Fetch many authors in one or more ``POST /author/batch`` calls.

        The API answers ``null`` for unknown ids; those entries are
        dropped. Requests chunk at 1000 ids (the API maximum) and are
        sent with retries.
        """
        results: list[Author] = []
        keys = list(dict.fromkeys(ids))
        if not keys:
            return results
        for start in range(0, len(keys), AUTHOR_BATCH_MAX_IDS):
            chunk = keys[start : start + AUTHOR_BATCH_MAX_IDS]
            params: dict[str, Any] | None = (
                {"fields": ",".join(fields)} if fields else None
            )
            response = await self._client.request(
                "POST",
                "author/batch",
                params=params,
                json={"ids": chunk},
                retry=True,
            )
            body = self._client.parse_json(response)
            records = (
                body
                if isinstance(body, list)
                else (body.get("data") if isinstance(body, dict) else None)
            )
            if not isinstance(records, list):
                raise ConfigurationError(
                    "POST /author/batch answered without a record list."
                )
            for record in records:
                if record is None:
                    continue
                results.append(
                    validate_model(
                        Author,
                        record,
                        request=getattr(response, "request", None),
                        response=response,
                    )
                )
        return results
