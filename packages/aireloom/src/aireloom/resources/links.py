"""Resource client for the Graph research-product links route."""

import logging
from collections.abc import Mapping
from typing import Any

from bibliofabric import ResourceClient
from pydantic import BaseModel, ValidationError as PydanticValidationError

from ..dialect import LINKS_DIALECT
from ..filters import LinksFilters
from ..models import Relation, RelationInfo

logger = logging.getLogger(__name__)


class LinksResource(ResourceClient[Relation]):
    """``/v3/research-products/links``: relations between research products.

    This route has no cursor and no sort parameter. Page windows are therefore
    not pinned: if the result ordering changes between requests, pages can
    shift and relations can be skipped or duplicated. The iterator stops on an
    empty page or when the reported total has been fetched, which bounds the
    walk but cannot remove that upstream hazard.
    """

    path = "v3/research-products/links"
    model = Relation
    dialect = LINKS_DIALECT
    filters_model = LinksFilters
    batch_size = 0

    async def get_relations_info(self) -> list[RelationInfo]:
        """Return the relation types the links endpoint can produce."""
        response = await self._client.request("GET", f"{self.path}/relations-info")
        info: list[RelationInfo] = []
        for entry in response.json():
            try:
                info.append(RelationInfo.model_validate(entry))
            except PydanticValidationError as error:
                logger.warning("Skipping invalid relations-info entry: %s", error)
        return info

    def build_filter_params(
        self, filters: BaseModel | Mapping[str, Any] | None
    ) -> dict[str, Any]:
        """Dump ``LinksFilters`` as individual query parameters."""
        if filters is None:
            return {}
        if isinstance(filters, LinksFilters):
            return {
                key: str(value)
                for key, value in filters.model_dump(exclude_none=True).items()
            }
        return dict(filters)
