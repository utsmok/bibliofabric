"""Clients for the account and prefix resources.

``/clients`` serves the repository accounts and ``/providers`` the members
behind them. ``/repositories`` is an alias of ``/clients`` that serves every
account, periodicals included. ``/prefixes`` serves the DOI prefixes, and
``/client-prefixes`` and ``/provider-prefixes`` the assignment ledger. The
account clients add ``activities()`` for the provenance log of one account;
the clients, providers, and prefixes clients add ``dois()`` and ``totals()``.
"""

from collections.abc import Mapping, Sequence
from dataclasses import replace
from typing import Any
from urllib.parse import quote

from bibliofabric import Page, validate_model
from bibliofabric.exceptions import ConfigurationError, ValidationError

from ..dialect import dialect_with
from ..filters import (
    ClientFilters,
    ClientPrefixFilters,
    PrefixFilters,
    ProviderFilters,
    ProviderPrefixFilters,
    RepositoryFilters,
    serialize_filter_params,
)
from ..models import (
    DataphoraActivity,
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
from .dois import ActivitiesClient, DoisClient


async def _totals(
    client: DataphoraResourceClient[Any],
    path: str,
    params: Mapping[str, str] | None = None,
) -> list[DataphoraTotals]:
    """Fetch and validate one ``/totals`` statistics route.

    The route answers a bare array of statistic entries, not a JSON:API
    envelope. Any other body raises ``ValidationError``.
    """
    response = await client._client.request("GET", path, params=params)
    body = client._client.parse_json(response)
    request = getattr(response, "request", None)
    if not isinstance(body, list):
        error = ValueError(f"expected a JSON array, got {type(body).__name__}")
        raise ValidationError(
            f"DataCite answered {path} without the expected JSON array.",
            raw=body,
            error=error,
            model_name="DataphoraTotals",
            request=request,
            response=response,
        )
    return [
        validate_model(DataphoraTotals, entry, request=request, response=response)
        for entry in body
    ]


async def _account_activities(
    client: DataphoraResourceClient[Any],
    route: str,
    id: str,
    page: int | None,
    page_size: int | None,
) -> Page[DataphoraActivity]:
    """Fetch one page of the activities of one account.

    The ``links.next`` link of these routes points at the global
    ``/activities`` route, so the returned page carries no cursor. Walk the
    account's activities with ``page=``.
    """
    account = client.normalize_id(id)
    if not account:
        raise ConfigurationError(
            f"{type(client).__name__}.activities requires a non-empty id."
        )
    scoped = ActivitiesClient(
        client._client, path=f"{route}/{quote(account, safe='')}/activities"
    )
    result = await scoped.search(page=page, page_size=page_size)
    return replace(result, next_cursor=None)


class ClientsClient(DataphoraResourceClient[DataphoraClientRecord]):
    """Client for the ``/clients`` endpoint."""

    path = "clients"
    model = DataphoraClientRecord
    dialect = dialect_with("fields[clients]")
    filters_model = ClientFilters

    async def totals(
        self,
        *,
        provider_id: str | Sequence[str] | None = None,
        state: str | None = None,
    ) -> list[DataphoraTotals]:
        """Return per-client DOI production statistics (``/clients/totals``).

        ``provider_id`` narrows the entries to the clients of one provider,
        or of several when it is a sequence. ``state`` is documented
        upstream, but without a login it does not change the answer. The
        answer is not paged; without a provider it is large (about 1.5 MB).
        """
        params = serialize_filter_params({"provider-id": provider_id, "state": state})
        return await _totals(self, "clients/totals", params or None)

    async def dois(self, id: str, **kwargs: Any) -> Page[DataphoraDoi]:
        """Return one page of the DOIs registered by this client.

        Keyword arguments forward to :meth:`bibliofabric.ResourceClient.search`
        (``query``, ``sort``, ``page_size``, ``cursor``, ``select``, and
        friends).
        """
        return await DoisClient(self._client).search({"client-id": id}, **kwargs)

    async def activities(
        self, id: str, *, page: int | None = None, page_size: int | None = None
    ) -> Page[DataphoraActivity]:
        """Return one page of the provenance activities of this client.

        Numbered paging only: upstream's next link leaves the client's own
        activities (see :func:`_account_activities`), so the page's
        ``next_cursor`` is always ``None``.
        """
        return await _account_activities(self, "clients", id, page, page_size)


class ProvidersClient(DataphoraResourceClient[DataphoraProvider]):
    """Client for the ``/providers`` endpoint."""

    path = "providers"
    model = DataphoraProvider
    dialect = dialect_with("fields[providers]")
    filters_model = ProviderFilters

    async def totals(self, *, state: str | None = None) -> list[DataphoraTotals]:
        """Return per-provider DOI production statistics (``/providers/totals``).

        ``state`` is documented upstream, but without a login it does not
        change the answer. The answer is not paged (about 0.6 MB).
        """
        params = serialize_filter_params({"state": state})
        return await _totals(self, "providers/totals", params or None)

    async def dois(self, id: str, **kwargs: Any) -> Page[DataphoraDoi]:
        """Return one page of the DOIs registered under this provider."""
        return await DoisClient(self._client).search({"provider-id": id}, **kwargs)

    async def activities(
        self, id: str, *, page: int | None = None, page_size: int | None = None
    ) -> Page[DataphoraActivity]:
        """Return one page of the provenance activities of this provider.

        Numbered paging only; the page's ``next_cursor`` is always ``None``
        (see :meth:`ClientsClient.activities`).
        """
        return await _account_activities(self, "providers", id, page, page_size)


class RepositoriesClient(DataphoraResourceClient[DataphoraRepository]):
    """Client for the ``/repositories`` endpoint.

    The route is an alias of ``/clients`` and serves every account,
    periodicals included; ids match :class:`ClientsClient` ids
    (``datacite.datacite``).
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

    async def totals(self, client_id: str | Sequence[str]) -> list[DataphoraTotals]:
        """Return DOI production statistics per prefix of one client.

        ``client_id`` is required: without ``client-id`` the route
        ``/prefixes/totals`` answers ``204 No Content`` (verified
        2026-11-28). A client without prefixes answers an empty list.
        """
        params = serialize_filter_params({"client-id": client_id})
        return await _totals(self, "prefixes/totals", params)

    async def dois(self, id: str, **kwargs: Any) -> Page[DataphoraDoi]:
        """Return one page of the DOIs registered under this prefix."""
        return await DoisClient(self._client).search({"prefix": id}, **kwargs)


class ClientPrefixesClient(DataphoraResourceClient[DataphoraClientPrefix]):
    """Client for the ``/client-prefixes`` endpoint."""

    path = "client-prefixes"
    model = DataphoraClientPrefix
    dialect = dialect_with("fields[client-prefixes]")
    filters_model = ClientPrefixFilters


class ProviderPrefixesClient(DataphoraResourceClient[DataphoraProviderPrefix]):
    """Client for the ``/provider-prefixes`` endpoint."""

    path = "provider-prefixes"
    model = DataphoraProviderPrefix
    dialect = dialect_with("fields[provider-prefixes]")
    filters_model = ProviderPrefixFilters


__all__ = [
    "ClientPrefixesClient",
    "ClientsClient",
    "PrefixesClient",
    "ProviderPrefixesClient",
    "ProvidersClient",
    "RepositoriesClient",
]
