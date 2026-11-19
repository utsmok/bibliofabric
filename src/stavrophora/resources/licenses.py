"""Licenses resource: the ``/licenses`` list route.

Crossref has no single-license route (verified live: ``/licenses/{id}``
returns 404); only the list endpoint exists.
"""

from ..dialect import CrossrefResourceClient
from ..models import License


class LicensesResource(CrossrefResourceClient[License]):
    """Typed client for the Crossref ``/licenses`` route (list/iterate only)."""

    path = "licenses"
    model = License
    supports_query = True
