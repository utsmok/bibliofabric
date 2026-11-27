"""Types resource: ``/types`` and the ``/types/{id}/works`` scope."""

from collections.abc import Mapping
from typing import Any
from urllib.parse import quote

from pydantic import BaseModel

from ..dialect import CrossrefUnpagedDialect
from ..models import CrossRefType
from .dialect import CrossrefResourceClient
from .works import ScopedWorksResource


class TypesResource(CrossrefResourceClient[CrossRefType]):
    """Typed client for the Crossref ``/types`` routes.

    The type list serves no ``query``, ``filter``, ``sort``, or ``select``;
    any of those parameters is rejected client-side. Crossref ignores
    ``rows`` and ``offset`` on ``/types`` and always returns the complete
    list in one response, so ``dialect`` is :data:`CrossrefUnpagedDialect`
    and ``count()`` and ``iterate()`` issue a single unpaged fetch.
    """

    path = "types"
    model = CrossRefType
    dialect = CrossrefUnpagedDialect

    def works(self, type_id: str | int) -> ScopedWorksResource:
        """Return a works client bound to ``types/{id}/works``."""
        type_id = quote(str(type_id).strip(), safe="")
        return ScopedWorksResource(self._client, path=f"types/{type_id}/works")

    async def count(
        self,
        filters: BaseModel | Mapping[str, Any] | None = None,
        *,
        query: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> int:
        """Return the total number of Crossref work types (single unpaged fetch)."""
        query_params = self._search_params(filters=filters, query=query, params=params)
        response = await self._client.request(
            "GET", self.path, params=query_params or None
        )
        body = self._client.parse_json(response)
        unwrapper = self._client.unwrapper
        total = unwrapper.total(body)
        return total if total is not None else len(unwrapper.results(body))
