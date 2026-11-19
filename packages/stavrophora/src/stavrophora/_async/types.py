"""Types resource: ``/types`` and the ``/types/{id}/works`` scope."""

from urllib.parse import quote

from ..models import CrossRefType
from .dialect import CrossrefResourceClient
from .works import ScopedWorksResource


class TypesResource(CrossrefResourceClient[CrossRefType]):
    """Typed client for the Crossref ``/types`` routes.

    The type list serves no ``query``, ``filter``, ``sort``, or ``select``;
    any of those parameters is rejected client-side.
    """

    path = "types"
    model = CrossRefType
    supports_query = False

    def works(self, type_id: str | int) -> ScopedWorksResource:
        """Return a works client bound to ``types/{id}/works``."""
        type_id = quote(str(type_id).strip(), safe="")
        return ScopedWorksResource(self._client, path=f"types/{type_id}/works")
