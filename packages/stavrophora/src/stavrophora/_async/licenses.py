"""Licenses resource: the ``/licenses`` list route.

Crossref has no single-license route (verified live: ``/licenses/{id}``
returns 404); only the list endpoint exists.
"""

from ..models import License
from .dialect import CrossrefResourceClient


class LicensesResource(CrossrefResourceClient[License]):
    """Typed client for the Crossref ``/licenses`` route (list/iterate only)."""

    path = "licenses"
    model = License
    supports_query = True
