"""Async Europe PMC client; the single source of truth for the sync twin."""

import logging
from functools import cached_property

import httpx
from bibliofabric import BaseApiClient

from ..config import EuropaeaSettings, get_settings
from .annotations import AnnotationsClient
from .articles import ArticlesClient
from .grants import GrantsClient
from .preprints import PreprintsClient
from .profiles import ProfilesClient
from .resources import EUROPEPMC_API_BASE_URL
from .search import SearchClient
from .unwrapper import EuropaeaUnwrapper

logger = logging.getLogger(__name__)


class EuropaeaClient(BaseApiClient):
    """Client for the Europe PMC REST web services.

    The API needs no credentials. The client sends ``Accept: application/json``
    on every request; the annotations API and the grants (Grist) API live on
    separate base URLs of the same host and are reachable through their
    resource clients.
    """

    def __init__(
        self,
        settings: EuropaeaSettings | None = None,
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
            base_url=base_url or EUROPEPMC_API_BASE_URL,
            settings=settings or get_settings(),
            unwrapper=EuropaeaUnwrapper(),
            http_client=http_client,
        )
        logger.debug("%s initialized.", type(self).__name__)

    @property
    def default_headers(self) -> dict[str, str]:
        """Headers sent with every request: the JSON representation."""
        return {"Accept": "application/json"}

    @cached_property
    def search(self) -> SearchClient:
        """The ``/search`` resource client."""
        return SearchClient(self)

    @cached_property
    def articles(self) -> ArticlesClient:
        """The per-article resource clients (record, XML, links, citations)."""
        return ArticlesClient(self)

    @cached_property
    def grants(self) -> GrantsClient:
        """The grants (Grist) API client."""
        return GrantsClient(self)

    @cached_property
    def profiles(self) -> ProfilesClient:
        """The ``/profile`` and ``/fields`` client."""
        return ProfilesClient(self)

    @cached_property
    def preprints(self) -> PreprintsClient:
        """The preprint-scoped search client."""
        return PreprintsClient(self)

    @cached_property
    def annotations(self) -> AnnotationsClient:
        """The annotations API client."""
        return AnnotationsClient(self)


__all__ = ["EuropaeaClient"]
