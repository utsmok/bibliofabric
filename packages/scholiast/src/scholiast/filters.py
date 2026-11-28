"""Filter criteria for the Semantic Scholar paper-search routes.

Every criterion becomes its own query parameter (``year=2020-2023``,
``minCitationCount=50``). Multi-value criteria are comma-joined strings,
as the API expects them (``fieldsOfStudy=Physics,Computer Science``).
Unknown extra keys pass through, so new API filters stay usable without a
package release.
"""

from pydantic import BaseModel, ConfigDict


class PaperSearchFilters(BaseModel):
    """Filters accepted by ``/paper/search`` and ``/paper/search/bulk``.

    String criteria take the API's own comma-joined syntax (for example
    ``year="2020-2023"``, ``venue="Nature,Science"``).
    """

    year: str | None = None
    venue: str | None = None
    fieldsOfStudy: str | None = None
    publicationTypes: str | None = None
    openAccessPdf: str | None = None
    minCitationCount: int | None = None

    model_config = ConfigDict(extra="allow")


__all__ = ["PaperSearchFilters"]
