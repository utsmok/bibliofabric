"""Client for the DataCite ``/dois`` endpoint."""

from typing import override

from bibliofabric import validate_model

from ..dialect import DATACITE_MAX_NUMBERED_RESULTS, dialect_with
from ..filters import DoiFilters
from ..models import DataphoraActivity, DataphoraDoi
from .dialect import DataphoraDoiClient


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
        """Return the provenance activities of one DOI, newest first.

        The route pages like every list route, so the method reads every
        page of up to 1000 records. The ``links.next`` link of these pages
        points at the global ``/activities`` route, so the method numbers
        the pages itself and stops at the first 10,000 records, the limit
        of numbered paging.
        """
        path = f"{self.item_path(doi)}/activities"
        activities: list[DataphoraActivity] = []
        page = 1
        pages = 1
        while page <= pages:
            response = await self._client.request(
                "GET", path, params={"page[number]": page, "page[size]": 1000}
            )
            body = self._client.parse_json(response)
            envelope = body.get("meta") if isinstance(body, dict) else None
            total_pages = (
                envelope.get("totalPages") if isinstance(envelope, dict) else None
            )
            if isinstance(total_pages, int):
                pages = min(total_pages, DATACITE_MAX_NUMBERED_RESULTS // 1000)
            records = self._client.unwrapper.results(body)
            activities.extend(
                validate_model(
                    DataphoraActivity,
                    record,
                    request=getattr(response, "request", None),
                    response=response,
                )
                for record in records
            )
            page += 1
        return activities


class ActivitiesClient(DataphoraDoiClient[DataphoraActivity]):
    """Client for the global ``/activities`` endpoint.

    For the activities of one DOI, prefer
    :meth:`DoisClient.activities`; this client lists and fetches
    activities across all DOIs. The route accepts ``page[size]``,
    ``page[number]``, and ``page[cursor]``. Without a login its ``id`` and
    ``ids[]`` filters answer nothing, so the client has no typed filter
    model; narrow a search with ``query`` and quote a value that contains
    a slash (``query='"10.5438/0012"'``), because the bare value is a
    400. Fetch one activity with ``get()``.
    """

    path = "activities"
    model = DataphoraActivity
    dialect = dialect_with("fields[activities]")

    @override
    def normalize_id(self, value: str) -> str:
        """Return the activity id unchanged (uuids, kept verbatim)."""
        return value.strip()


__all__ = ["ActivitiesClient", "DoisClient"]
