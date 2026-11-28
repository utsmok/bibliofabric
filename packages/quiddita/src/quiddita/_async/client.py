"""Async Wikidata client; the single source of truth for the sync twin."""

import logging
from functools import cached_property
from typing import override

import httpx
from bibliofabric import BaseApiClient

from ..config import QuidditaSettings, get_settings
from ..dialect import ACTION_API_BASE_URL, SPARQL_BASE_URL
from ..unwrapper import QuidditaUnwrapper
from .claims import ClaimsClient
from .entities import EntitiesClient
from .entity_data import EntityDataClient
from .lexemes import LexemesClient
from .rest_items import ItemsClient, PropertiesClient
from .search import SearchClient
from .sitelinks import SitelinksClient
from .sparql import SparqlClient
from .statements import StatementsClient
from .utilities import UtilitiesClient

logger = logging.getLogger(__name__)


class QuidditaQueryClient(BaseApiClient):
    """Client for the SPARQL query service host (``query.wikidata.org``).

    The main :class:`QuidditaClient` builds one instance of this class for
    its ``sparql`` resource. The instance shares the settings object with the
    main client and runs its requests in the ``sparql`` rate class of the
    main client's limiter, so the two hosts together stay inside the pace the
    settings describe.
    """

    def __init__(
        self,
        settings: QuidditaSettings | None = None,
        *,
        limiter: object | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Build the query client.

        Args:
            settings: Settings instance; ``None`` loads from the environment.
            limiter: The main client's limiter to share (internal wiring;
                ``None`` builds one from ``settings``).
            http_client: Optional pre-configured ``httpx.AsyncClient`` (the
                caller retains ownership and closes it).
        """
        super().__init__(
            base_url=SPARQL_BASE_URL,
            settings=settings or get_settings(),
            unwrapper=QuidditaUnwrapper(),
            http_client=http_client,
        )
        if limiter is not None:
            self._limiter = limiter
        logger.debug("%s initialized.", type(self).__name__)

    @property
    def default_headers(self) -> dict[str, str]:
        """Headers sent with every request: the SPARQL JSON representation."""
        return {"Accept": "application/sparql-results+json"}

    @override
    def rate_class(self, request: httpx.Request) -> str:
        """Route every request through the ``sparql`` rate class."""
        return "sparql"


class QuidditaClient(BaseApiClient):
    """Client for Wikidata: the Action API, the Wikibase REST API, and SPARQL.

    The API needs no credentials, but all three services ask for a
    descriptive ``User-Agent`` with contact information; the client builds it
    from the settings. ``www.wikidata.org`` serves both the Action API
    (``w/api.php``) and the Wikibase REST API (``w/rest.php/wikibase/v1``),
    so one client covers them. SPARQL lives on ``query.wikidata.org`` and is
    reached through ``client.sparql``.
    """

    def __init__(
        self,
        settings: QuidditaSettings | None = None,
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
        self._own_settings = settings or get_settings()
        super().__init__(
            base_url=base_url or ACTION_API_BASE_URL,
            settings=self._own_settings,
            unwrapper=QuidditaUnwrapper(),
            http_client=http_client,
        )
        logger.debug("%s initialized.", type(self).__name__)

    @property
    def default_headers(self) -> dict[str, str]:
        """Headers sent with every request: the JSON representation."""
        return {"Accept": "application/json"}

    @cached_property
    def _query_client(self) -> QuidditaQueryClient:
        """The second-host SPARQL client, sharing settings and limiter."""
        return QuidditaQueryClient(
            settings=self._own_settings,
            limiter=self._limiter,
        )

    @cached_property
    def sparql(self) -> SparqlClient:
        """The SPARQL query service on ``query.wikidata.org``."""
        return SparqlClient(self._query_client)

    @cached_property
    def entities(self) -> EntitiesClient:
        """The ``wbgetentities`` resource: get, batch, and iterate ids."""
        return EntitiesClient(self)

    @cached_property
    def search(self) -> SearchClient:
        """The ``wbsearchentities`` and REST search resources."""
        return SearchClient(self)

    @cached_property
    def claims(self) -> ClaimsClient:
        """The ``wbgetclaims`` resource."""
        return ClaimsClient(self)

    @cached_property
    def sitelinks(self) -> SitelinksClient:
        """The ``wbgetentities`` site link resource."""
        return SitelinksClient(self)

    @cached_property
    def items(self) -> ItemsClient:
        """The Wikibase REST item routes."""
        return ItemsClient(self)

    @cached_property
    def properties(self) -> PropertiesClient:
        """The Wikibase REST property routes."""
        return PropertiesClient(self)

    @cached_property
    def statements(self) -> StatementsClient:
        """The Wikibase REST statement routes."""
        return StatementsClient(self)

    @cached_property
    def entity_data(self) -> EntityDataClient:
        """The ``Special:EntityData`` routes (full entity per format)."""
        return EntityDataClient(self)

    @cached_property
    def lexemes(self) -> LexemesClient:
        """The WikibaseLexeme REST read routes."""
        return LexemesClient(self)

    @cached_property
    def utilities(self) -> UtilitiesClient:
        """The Action API utility read modules (badges, format, parse,
        suggestions, constraints)."""
        return UtilitiesClient(self)

    @override
    async def aclose(self) -> None:
        """Close the HTTP clients of both hosts when owned."""
        query_client = self.__dict__.get("_query_client")
        if query_client is not None:
            await query_client.aclose()
        await super().aclose()


__all__ = ["QuidditaClient", "QuidditaQueryClient"]
