"""Client for the DataCite ``/dois`` endpoint."""

from typing import override

from ..dialect import dialect_with
from ..filters import DoiFilters
from ..models import DataphoraActivity, DataphoraDoi
from .dialect import DataphoraDoiClient

ACTIVITIES_PATH = "dois/{doi}/activities"


class DoisClient(DataphoraDoiClient[DataphoraDoi]):
    """Client for the ``/dois`` endpoint.

    Generic operations (``get``, ``exists``, ``search``, ``iterate``,
    ``collect``, ``first``, ``count``) come from
    :class:`bibliofabric.ResourceClient`. ``iterate()`` walks with
    ``page[cursor]`` so it can pass the 10,000-record limit of numbered
    paging; cursor walks always run in ``created`` ascending order.
    """

    path = "dois"
    model = DataphoraDoi
    dialect = dialect_with("fields[dois]")
    filters_model = DoiFilters

    async def activities(self, doi: str) -> list[DataphoraActivity]:
        """Return the provenance activities of one DOI, oldest first."""
        path = ACTIVITIES_PATH.format(doi=self.normalize_id(doi))
        response = await self._client.request("GET", path)
        body = self._client.parse_json(response)
        records = self._client.unwrapper.results(body)
        return [DataphoraActivity.model_validate(record) for record in records]


class ActivitiesClient(DataphoraDoiClient[DataphoraActivity]):
    """Client for the global ``/activities`` endpoint.

    For the activities of one DOI, prefer
    :meth:`DoisClient.activities`; this client lists and fetches
    activities across all DOIs.
    """

    path = "activities"
    model = DataphoraActivity
    dialect = dialect_with("fields[activities]")

    @override
    def normalize_id(self, value: str) -> str:
        """Return the activity id unchanged (uuids, kept verbatim)."""
        return value.strip()


__all__ = ["ActivitiesClient", "DoisClient"]
