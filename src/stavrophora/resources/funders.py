"""Funders resource: ``/funders`` and the ``/funders/{id}/works`` scope."""

from urllib.parse import quote

from bibliofabric.ids import normalize_doi

from ..dialect import CrossrefResourceClient
from ..filters import FunderFilters
from ..models import Funder
from .works import ScopedWorksResource


class FundersResource(CrossrefResourceClient[Funder]):
    """Typed client for the Crossref ``/funders`` routes.

    Accepts plain ``query`` plus the ``location`` filter.
    """

    path = "funders"
    model = Funder
    filters_model = FunderFilters
    supports_query = True
    supports_filter = True

    def normalize_id(self, value: str | int) -> str:
        """Return the bare lowercase funder DOI."""
        return normalize_doi(str(value))

    def works(self, funder_id: str) -> ScopedWorksResource:
        """Return a works client bound to ``funders/{id}/works``.

        ``funder_id`` is the funder's Funder Registry DOI.
        """
        funder_id = quote(normalize_doi(funder_id), safe="")
        return ScopedWorksResource(self._client, path=f"funders/{funder_id}/works")
