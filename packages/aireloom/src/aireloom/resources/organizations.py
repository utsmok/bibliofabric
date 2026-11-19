"""Resource client for OpenAIRE organizations (V4)."""

from collections.abc import Sequence

from ..filters import OrganizationsFilters
from ..models import Organization
from .base import GraphResource


class OrganizationsResource(GraphResource[Organization]):
    """V4 organizations endpoint: search, iterate, count, facets, group_by.

    ``get(id)`` reads the V3 by-id route because V4 has no by-id endpoints.
    """

    path = "v4/organizations"
    model = Organization
    filters_model = OrganizationsFilters

    async def find_variants(
        self, names: Sequence[str], *, country: str | None = None
    ) -> list[Organization]:
        """Search each name fragment and return deduplicated organizations.

        Records are deduplicated by exact ``id`` keeping the first match;
        ``pending_org_::`` records are kept on purpose. They carry
        organization-project links that the canonical merged record lost,
        which makes them the main source of undercounted org-project
        links, so callers decide how to merge them.
        """
        filters = {"country": country} if country else None
        found: dict[str, Organization] = {}
        for name in names:
            page = await self.search(filters, query=name)
            for org in page.results:
                found.setdefault(org.id, org)
        return list(found.values())
