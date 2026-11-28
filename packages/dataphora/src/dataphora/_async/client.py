"""Async DataCite REST API client; the single source of truth for the sync twin."""

import logging
from functools import cached_property

import httpx
from bibliofabric import BaseApiClient
from bibliofabric.unwrap import JsonApiUnwrapper

from ..config import DataphoraSettings, get_settings
from ..dialect import DATACITE_API_BASE_URL, DATACITE_HEARTBEAT_PATH
from .dois import ActivitiesClient, DoisClient
from .events import EventsClient
from .graphql import GraphqlClient
from .registry import (
    ClientPrefixesClient,
    ClientsClient,
    PrefixesClient,
    ProviderPrefixesClient,
    ProvidersClient,
    RepositoriesClient,
)

logger = logging.getLogger(__name__)


class DataphoraClient(BaseApiClient):
    """Client for the DataCite REST API.

    Public reads need no credentials. The client sends
    ``Accept: application/vnd.api+json`` on every request and paces itself
    at the anonymous limit documented by DataCite (500 requests per 5
    minutes) by default.
    """

    def __init__(
        self,
        settings: DataphoraSettings | None = None,
        *,
        base_url: str | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Build the client.

        Args:
            settings: Settings instance; ``None`` loads from the environment.
            base_url: API base URL override (testing).
            http_client: Optional pre-configured ``httpx.AsyncClient`` (caller
                retains ownership and is responsible for closing it).
        """
        super().__init__(
            base_url=base_url or DATACITE_API_BASE_URL,
            settings=settings or get_settings(),
            unwrapper=JsonApiUnwrapper(cursor_param="page[cursor]"),
            http_client=http_client,
        )
        logger.debug("%s initialized.", type(self).__name__)

    @property
    def default_headers(self) -> dict[str, str]:
        """Headers sent with every request: the JSON:API representation."""
        return {"Accept": "application/vnd.api+json"}

    @cached_property
    def dois(self) -> DoisClient:
        """The DOIs resource client."""
        return DoisClient(self)

    @cached_property
    def activities(self) -> ActivitiesClient:
        """The global activities resource client."""
        return ActivitiesClient(self)

    @cached_property
    def clients(self) -> ClientsClient:
        """The repository accounts resource client."""
        return ClientsClient(self)

    @cached_property
    def client_prefixes(self) -> ClientPrefixesClient:
        """The client prefix assignments resource client."""
        return ClientPrefixesClient(self)

    @cached_property
    def providers(self) -> ProvidersClient:
        """The DataCite members resource client."""
        return ProvidersClient(self)

    @cached_property
    def provider_prefixes(self) -> ProviderPrefixesClient:
        """The provider prefix assignments resource client."""
        return ProviderPrefixesClient(self)

    @cached_property
    def repositories(self) -> RepositoriesClient:
        """The re3data/OpenDOAR repository view resource client."""
        return RepositoriesClient(self)

    @cached_property
    def prefixes(self) -> PrefixesClient:
        """The DOI prefixes resource client."""
        return PrefixesClient(self)

    @cached_property
    def events(self) -> EventsClient:
        """The citation events resource client."""
        return EventsClient(self)

    @cached_property
    def graphql(self) -> GraphqlClient:
        """The public GraphQL API client."""
        return GraphqlClient(self)

    async def heartbeat(self) -> bool:
        """Return ``True`` when the API answers ``GET /heartbeat`` with ``OK``.

        The route needs no credentials and answers a plain ``OK``. An error
        status raises, as with every request.
        """
        response = await self.request("GET", DATACITE_HEARTBEAT_PATH)
        return response.text.strip() == "OK"


__all__ = ["DataphoraClient"]
