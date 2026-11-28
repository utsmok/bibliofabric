"""The answer of the ``/ra/`` registration agency lookup."""

from pydantic import BaseModel, ConfigDict


class AgencyAnswer(BaseModel):
    """One entry of the ``GET /ra/{doi}`` JSON list.

    A known DOI carries the registration agency name in ``RA`` (for example
    ``Crossref``, ``DataCite``, ``mEDRA``). An unknown or malformed DOI has
    ``RA=None`` and a ``status`` string (``DOI does not exist``,
    ``Invalid DOI``, or ``Unknown``). The HTTP status is 200 in every case.
    """

    DOI: str
    RA: str | None = None
    status: str | None = None

    model_config = ConfigDict(extra="allow")
