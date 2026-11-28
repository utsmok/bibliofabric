"""Filter criteria for the Semantic Scholar paper-search routes.

Every criterion becomes its own query parameter (``year=2020-2023``,
``minCitationCount=50``). Multi-value criteria are comma-joined strings,
as the API expects them (``fieldsOfStudy=Physics,Computer Science``).
Unknown extra keys pass through, so new API filters stay usable without a
package release.
"""

from pydantic import BaseModel, ConfigDict


class PaperSearchFilters(BaseModel):
    """Filters accepted by ``/paper/search``, ``/paper/search/bulk``, and
    ``/paper/search/match``.

    String criteria take the API's own comma-joined syntax (for example
    ``year="2020-2023"``, ``venue="Nature,Science"``,
    ``publicationDateOrYear="2020-06:2021"``). ``openAccessPdf`` is a flag
    the API documents without a value; pass ``""`` to restrict the results
    to papers with a public PDF.
    """

    year: str | None = None
    venue: str | None = None
    fieldsOfStudy: str | None = None
    publicationTypes: str | None = None
    openAccessPdf: str | None = None
    minCitationCount: int | None = None
    publicationDateOrYear: str | None = None

    model_config = ConfigDict(extra="allow")


__all__ = ["PaperSearchFilters"]
