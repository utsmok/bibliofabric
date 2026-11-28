"""Async Semantic Scholar client; the single source of truth for the sync twin."""

import logging
from functools import cached_property

import httpx
from bibliofabric import BaseApiClient

from ..config import ScholiastSettings, get_settings
from ..dialect import SEMANTICSCHOLAR_GRAPH_BASE_URL
from ..unwrapper import ScholiastUnwrapper
from .authors import AuthorsClient
from .datasets import DatasetsClient
from .papers import PapersClient
from .patents import PatentsClient
from .recommendations import RecommendationsClient
from .snippets import SnippetsClient

logger = logging.getLogger(__name__)


class ScholiastClient(BaseApiClient):
    """Client for the Semantic Scholar Academic Graph API.

    The API key is optional. When the settings carry one, the client
    sends it in the ``x-api-key`` header on every request and the caller
    gets a guaranteed 1 request per second allocation. Without a key the
    client runs on the shared anonymous pool, where any request may
    answer HTTP 429.
    """

    def __init__(
        self,
        settings: ScholiastSettings | None = None,
        *,
        base_url: str | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Build the client.

        Args:
            settings: Settings instance; ``None`` loads from the environment.
            base_url: Graph API base URL override (testing).
            http_client: Optional pre-configured ``httpx.AsyncClient`` (caller
                retains ownership and is responsible for closing it).
        """
        super().__init__(
            base_url=base_url or SEMANTICSCHOLAR_GRAPH_BASE_URL,
            settings=settings or get_settings(),
            unwrapper=ScholiastUnwrapper(),
            http_client=http_client,
        )
        self._settings_typed = settings or get_settings()
        logger.debug("%s initialized.", type(self).__name__)

    @property
    def default_headers(self) -> dict[str, str]:
        """Headers sent with every request: the API key when one is set."""
        api_key = self._settings_typed.api_key
        if api_key is not None:
            return {"x-api-key": api_key.get_secret_value()}
        return {}

    @cached_property
    def papers(self) -> PapersClient:
        """The papers resource client."""
        return PapersClient(self)

    @cached_property
    def authors(self) -> AuthorsClient:
        """The authors resource client."""
        return AuthorsClient(self)

    @cached_property
    def recommendations(self) -> RecommendationsClient:
        """The recommendations client (its own base URL)."""
        return RecommendationsClient(self)

    @cached_property
    def datasets(self) -> DatasetsClient:
        """The datasets client (its own base URL)."""
        return DatasetsClient(self)

    @cached_property
    def snippets(self) -> SnippetsClient:
        """The snippet search client."""
        return SnippetsClient(self)

    @cached_property
    def patents(self) -> PatentsClient:
        """The patents client."""
        return PatentsClient(self)


__all__ = ["ScholiastClient"]
