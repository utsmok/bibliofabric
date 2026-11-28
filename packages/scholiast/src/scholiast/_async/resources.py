"""Resource base shared by the Semantic Scholar resources.

The Academic Graph names its query parameters close to the bibliofabric
defaults: ``query`` for free text, ``limit`` for page size, ``offset`` for
paging, and ``fields`` for field selection, so the shared
:class:`SEMANTICSCHOLAR_DIALECT` needs no per-resource overrides. The two
adjustments live here: record ids travel verbatim (``DOI:10.1/x``,
``ARXIV:2106.15928`` contain characters other APIs strip), and ``exists()``
uses ``GET`` because the gateway answers ``HEAD`` with 405.
"""

from collections.abc import Mapping, Sequence
from typing import Any, override

from bibliofabric import ResourceClient, validate_model
from bibliofabric.exceptions import NotFoundError
from bibliofabric.paging import Page
from pydantic import BaseModel

from ..dialect import SEMANTICSCHOLAR_DIALECT


def _response_request(response: Any) -> Any:
    try:
        return response.request
    except RuntimeError:
        return None


async def fetch_list_page[E: BaseModel](
    client: Any,
    path: str,
    model: type[E],
    *,
    fields: Sequence[str] | None = None,
    limit: int | None = None,
    offset: int | None = None,
    query: str | None = None,
    extra_params: Mapping[str, Any] | None = None,
) -> Page[E]:
    """Fetch one ``{data, next, offset}`` page from a sub-list route.

    The citations, references, author-papers, and author-search routes
    share this envelope. ``total`` exists only on search routes; this
    helper reports ``None`` when the envelope lacks it.
    """
    params: dict[str, Any] = dict(extra_params or {})
    if fields:
        params["fields"] = ",".join(fields)
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    if query is not None:
        params["query"] = query
    response = await client.request("GET", path, params=params)
    body = client.parse_json(response)
    unwrapper = client.unwrapper
    records = unwrapper.results(body)
    results = [
        validate_model(
            model, record, request=_response_request(response), response=response
        )
        for record in records
    ]
    return Page(
        results=results,
        total=unwrapper.total(body),
        next_cursor=unwrapper.next_cursor(body),
        page=None,
        meta=unwrapper.meta(body),
    )


class ScholiastResourceClient[E: BaseModel](ResourceClient[E]):
    """Base client for Academic Graph resources: dialect and id handling."""

    dialect = SEMANTICSCHOLAR_DIALECT

    @override
    def normalize_id(self, value: str) -> str:
        """Return the id unchanged; Semantic Scholar ids are exact strings."""
        return value

    @override
    async def exists(self, id: str | int) -> bool:
        """Return ``True`` when ``id`` exists; 404 returns ``False``.

        Uses ``GET`` because the API gateway answers ``HEAD`` with 405.
        """
        try:
            await self.get(id)
        except NotFoundError:
            return False
        return True


__all__ = [
    "ScholiastResourceClient",
    "fetch_list_page",
]
