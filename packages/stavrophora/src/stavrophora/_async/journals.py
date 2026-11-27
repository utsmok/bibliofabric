"""Journals resource: ``/journals`` and the ``/journals/{issn}/works`` scope."""

from urllib.parse import quote

from bibliofabric.ids import normalize_issn

from ..models import Journal
from .dialect import CrossrefResourceClient
from .works import ScopedWorksResource


class JournalsResource(CrossrefResourceClient[Journal]):
    """Typed client for the Crossref ``/journals`` routes.

    Accepts plain ``query`` only; ``filter``, ``sort``, and ``select`` are
    rejected client-side because the route returns 400 for them.
    """

    path = "journals"
    model = Journal

    def normalize_id(self, value: str | int) -> str:
        """Return the hyphenated uppercase ISSN form."""
        return normalize_issn(str(value))

    async def dois_by_year(self, issn: str) -> dict[int, int]:
        """Return DOI counts per issued year from the journal record.

        Reads ``breakdowns.dois-by-issued-year`` from ``/journals/{issn}``.
        Returns an empty dict when the record carries no breakdown.
        """
        journal = await self.get(issn)
        if journal.breakdowns is None:
            return {}
        return dict(journal.breakdowns.dois_by_issued_year)

    def works(self, issn: str) -> ScopedWorksResource:
        """Return a works client bound to ``journals/{issn}/works``.

        Accepts print or electronic ISSNs; hyphens and case are normalized.
        """
        issn = quote(normalize_issn(issn), safe="")
        return ScopedWorksResource(self._client, path=f"journals/{issn}/works")
