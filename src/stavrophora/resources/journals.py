"""Journals resource: ``/journals`` and the ``/journals/{issn}/works`` scope."""

from urllib.parse import quote

from bibliofabric.ids import normalize_issn

from ..dialect import CrossrefResourceClient
from ..models import Journal
from .works import ScopedWorksResource


class JournalsResource(CrossrefResourceClient[Journal]):
    """Typed client for the Crossref ``/journals`` routes.

    Accepts plain ``query`` only; ``filter``, ``sort``, and ``select`` are
    rejected client-side because the route returns 400 for them.
    """

    path = "journals"
    model = Journal
    supports_query = True

    def normalize_id(self, value: str) -> str:
        """Return the hyphenated uppercase ISSN form."""
        return normalize_issn(value)

    def works(self, issn: str) -> ScopedWorksResource:
        """Return a works client bound to ``journals/{issn}/works``.

        Accepts print or electronic ISSNs; hyphens and case are normalized.
        """
        issn = quote(normalize_issn(issn), safe="")
        return ScopedWorksResource(self._client, f"journals/{issn}/works")
