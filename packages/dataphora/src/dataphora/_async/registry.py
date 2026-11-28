"""Clients for the account and prefix resources.

The ``/clients``, ``/providers``, and ``/repositories`` routes serve the
same repository accounts from different angles; ``/prefixes`` serves DOI
prefixes. Each client adds ``dois()`` to read the DOIs of one account or
prefix through the route's own filter.
"""

from http import HTTPStatus
from typing import Any

from bibliofabric import Page, validate_model

from ..dialect import dialect_with
from ..filters import ClientFilters, PrefixFilters, ProviderFilters, RepositoryFilters
from ..models import (
    DataphoraClientPrefix,
    DataphoraClientRecord,
    DataphoraDoi,
    DataphoraPrefix,
    DataphoraProvider,
    DataphoraProviderPrefix,
    DataphoraRepository,
    DataphoraTotals,
)
from .dialect import DataphoraResourceClient
from .dois import DoisClient


async def _totals(client: DataphoraResourceClient, path: str) -> list[DataphoraTotals]:
    """Fetch and validate one ``/totals`` statistics route.

    The route answers a bare array of statistic entries, not a JSON:API
    envelope.
    """
    response = await client._client.request("GET", path)
    body = client._client.parse_json(response)
    if not isinstance(body, list):
        return []
    return [validate_model(DataphoraTotals, entry, response=response) for entry in body]


class ClientsClient(DataphoraResourceClient[DataphoraClientRecord]):
    """Client for the ``/clients`` endpoint."""

    path = "clients"
    model = DataphoraClientRecord
    dialect = dialect_with("fields[clients]")
    filters_model = ClientFilters

    async def totals(self) -> list[DataphoraTotals]:
        """Return per-client DOI production statistics (``/clients/totals``).

        The response is large (one entry per client) and not paged.
        """
        return await _totals(self, "clients/totals")

    async def dois(self, id: str, **kwargs: Any) -> Page[DataphoraDoi]:
        """Return one page of the DOIs registered by this client.

        Keyword arguments forward to :meth:`bibliofabric.ResourceClient.search`
        (``query``, ``sort``, ``page_size``, ``cursor``, ``select``, and
        friends).
        """
        return await DoisClient(self._client).search({"client-id": id}, **kwargs)


class ProvidersClient(DataphoraResourceClient[DataphoraProvider]):
    """Client for the ``/providers`` endpoint."""

    path = "providers"
    model = DataphoraProvider
    dialect = dialect_with("fields[providers]")
    filters_model = ProviderFilters

    async def totals(self) -> list[DataphoraTotals]:
        """Return per-provider DOI production statistics (``/providers/totals``)."""
        return await _totals(self, "providers/totals")

    async def dois(self, id: str, **kwargs: Any) -> Page[DataphoraDoi]:
        """Return one page of the DOIs registered under this provider."""
        return await DoisClient(self._client).search({"provider-id": id}, **kwargs)


class RepositoriesClient(DataphoraResourceClient[DataphoraRepository]):
    """Client for the ``/repositories`` endpoint.

    A repository is the re3data/OpenDOAR view of a client; ids match
    ``ClientsClient`` ids (``datacite.datacite``).
    """

    path = "repositories"
    model = DataphoraRepository
    dialect = dialect_with("fields[repositories]")
    filters_model = RepositoryFilters

    async def dois(self, id: str, **kwargs: Any) -> Page[DataphoraDoi]:
        """Return one page of the DOIs registered by this repository."""
        return await DoisClient(self._client).search({"client-id": id}, **kwargs)


class PrefixesClient(DataphoraResourceClient[DataphoraPrefix]):
    """Client for the ``/prefixes`` endpoint."""

    path = "prefixes"
    model = DataphoraPrefix
    dialect = dialect_with("fields[prefixes]")
    filters_model = PrefixFilters

    async def totals(self) -> list[DataphoraTotals]:
        """Return per-prefix DOI production statistics (``/prefixes/totals``).

        The route answers ``204 No Content`` for anonymous callers on the
        production API (verified 2026-11-27), so the result is empty there
        without a login.
        """
        response = await self._client.request("GET", "prefixes/totals")
        if response.status_code == HTTPStatus.NO_CONTENT:
            return []
        body = self._client.parse_json(response)
        if not isinstance(body, list):
            return []
        return [
            validate_model(DataphoraTotals, entry, response=response) for entry in body
        ]

    async def dois(self, id: str, **kwargs: Any) -> Page[DataphoraDoi]:
        """Return one page of the DOIs registered under this prefix."""
        return await DoisClient(self._client).search({"prefix": id}, **kwargs)


class ClientPrefixesClient(DataphoraResourceClient[DataphoraClientPrefix]):
    """Client for the ``/client-prefixes`` endpoint."""

    path = "client-prefixes"
    model = DataphoraClientPrefix
    dialect = dialect_with("fields[client-prefixes]")


class ProviderPrefixesClient(DataphoraResourceClient[DataphoraProviderPrefix]):
    """Client for the ``/provider-prefixes`` endpoint."""

    path = "provider-prefixes"
    model = DataphoraProviderPrefix
    dialect = dialect_with("fields[provider-prefixes]")


__all__ = [
    "ClientPrefixesClient",
    "ClientsClient",
    "PrefixesClient",
    "ProviderPrefixesClient",
    "ProvidersClient",
    "RepositoriesClient",
]
