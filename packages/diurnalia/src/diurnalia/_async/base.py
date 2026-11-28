"""Resource base shared by the DOAJ resources.

DOAJ differs from the bibliofabric defaults in one structural way: the
search query travels in the path (``/search/journals/{query}``) instead of
a query parameter. There is no ISSN or DOI route, so ``get()`` on each
resource runs a fielded search. The record routes (``/journals/{id}`` and
``/articles/{id}``) take the DOAJ record id and answer more fields than a
search result.
"""

from typing import ClassVar, override
from urllib.parse import quote

import httpx
from bibliofabric import ResourceClient
from bibliofabric.exceptions import ConfigurationError, NotFoundError
from pydantic import BaseModel

from ..dialect import DOAJ_DIALECT


def quote_query(query: str | None) -> str:
    """Return the path segment for a query; a missing query is match-all ``*``."""
    return quote(query, safe="") if query else "*"


class DiurnaliaResourceClient[E: BaseModel](ResourceClient[E]):
    """Base client for DOAJ resources: query-in-path and search-based ``get()``."""

    dialect = DOAJ_DIALECT
    search_prefix: ClassVar[str]
    """Path prefix of the search route, ``search/journals`` or ``search/articles``."""
    record_path: ClassVar[str]
    """Path prefix of the record route, ``journals`` or ``articles``."""

    @override
    def search_path(self, query: str | None) -> str:
        """Return ``{search_prefix}/{quoted query}``; a missing query is ``*``."""
        return f"{self.search_prefix}/{quote_query(query)}"

    @override
    def normalize_id(self, value: str) -> str:
        """Return the value unchanged; ids here are ISSNs or DOIs."""
        return value

    @override
    async def exists(self, id: str | int) -> bool:
        """Return ``True`` when the identifier matches a record.

        Uses the search route; a query without results returns ``False``.
        """
        try:
            await self.get(str(id))
        except NotFoundError:
            return False
        return True

    async def get_by_id(self, id: str) -> E:
        """Return the full record behind a DOAJ record id.

        A search result carries the id as ``id``. The record route adds
        fields that the search result lacks, such as ``es_type`` and the
        editorial flags in ``admin``. Raises ``NotFoundError`` when no
        record has the id.
        """
        if not id:
            raise ConfigurationError(
                f"{type(self).__name__}.get_by_id requires a non-empty id."
            )
        response = await self._client.request(
            "GET", f"{self.record_path}/{quote(id, safe='')}"
        )
        body = self._client.parse_json(response)
        try:
            request: httpx.Request | None = response.request
        except RuntimeError:
            request = None
        return self._validate(body, request=request, response=response)


__all__ = ["DiurnaliaResourceClient", "quote_query"]
