"""Resource base shared by the DataCite resources.

DataCite filters travel as one query parameter per criterion (the framework
default dumps one value per key), sequence values join with commas, and
every resource names its own sparse-fieldset parameter
(``fields[dois]``, ``fields[clients]``).
"""

from collections.abc import Mapping, Sequence
from typing import Any, override

from bibliofabric import ResourceClient
from bibliofabric.exceptions import ConfigurationError
from bibliofabric.ids import normalize_doi
from pydantic import BaseModel

from ..dialect import DATACITE_DIALECT, DATACITE_MAX_NUMBERED_RESULTS, dialect_with
from ..filters import serialize_filter_params


class DataphoraResourceClient[E: BaseModel](ResourceClient[E]):
    """Base client for DataCite resources: filter serialization and dialect.

    ``batch_get()`` is disabled (``batch_size = 0``): DataCite has no route
    that reads several records by id, and it silently ignores unknown query
    parameters.
    """

    dialect = DATACITE_DIALECT
    batch_size = 0

    @override
    def build_filter_params(
        self, filters: BaseModel | Mapping[str, Any] | None
    ) -> dict[str, str]:
        """Convert filter criteria into DataCite query parameters."""
        return serialize_filter_params(filters)

    def _search_params(
        self,
        *,
        filters: BaseModel | Mapping[str, Any] | None,
        query: str | None = None,
        sort: str | Sequence[str] | None = None,
        select: Sequence[str] | None = None,
        page: int | None = None,
        page_size: int | None = None,
        cursor: str | None = None,
        params: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        """Build the query parameters and guard numbered paging.

        Upstream reads ``page[number]=0`` as page 1 and answers a page that
        reaches past record 10,000 with the last reachable page again. Both
        raise ``ConfigurationError`` here instead of returning the wrong page.
        """
        if cursor is None and page is not None:
            first = self.dialect.page_start
            if page < first:
                raise ConfigurationError(f"page must be >= {first}, got {page}.")
            size = (
                self.dialect.default_page_size
                if page_size is None
                else min(page_size, self.dialect.max_page_size)
            )
            if (page - first + 1) * size > DATACITE_MAX_NUMBERED_RESULTS:
                raise ConfigurationError(
                    f"DataCite serves numbered pages up to record "
                    f"{DATACITE_MAX_NUMBERED_RESULTS} (requested page={page}, "
                    f"page_size={size}); use iterate() or cursor= for deeper "
                    "pages."
                )
        return super()._search_params(
            filters=filters,
            query=query,
            sort=sort,
            select=select,
            page=page,
            page_size=page_size,
            cursor=cursor,
            params=params,
        )


class DataphoraDoiClient[E: BaseModel](DataphoraResourceClient[E]):
    """Base for resources that address DOIs: DOI id normalization."""

    dialect = dialect_with("fields[dois]")

    @override
    def normalize_id(self, value: str) -> str:
        """Return the bare lowercase DOI (``https://doi.org/10.5438/0012``
        becomes ``10.5438/0012``)."""
        return normalize_doi(value)


__all__ = ["DataphoraDoiClient", "DataphoraResourceClient"]
