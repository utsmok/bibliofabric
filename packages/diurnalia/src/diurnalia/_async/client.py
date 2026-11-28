"""Async DOAJ client; the single source of truth for the sync twin."""

import logging
from functools import cached_property

import httpx
from bibliofabric import BaseApiClient

from ..config import DiurnaliaSettings, get_settings
from ..dialect import DOAJ_API_BASE_URL
from ..unwrapper import DiurnaliaUnwrapper
from .articles import ArticlesClient
from .base import DiurnaliaResourceClient
from .journals import JournalsClient

logger = logging.getLogger(__name__)


class DiurnaliaClient(BaseApiClient):
    """Client for the DOAJ API version 4.

    The search routes need no credentials. The client sends ``Accept:
    application/json`` on every request and paces requests at half of the
    documented limit of two per second by default.
    """

    def __init__(
        self,
        settings: DiurnaliaSettings | None = None,
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
            base_url=base_url or DOAJ_API_BASE_URL,
            settings=settings or get_settings(),
            unwrapper=DiurnaliaUnwrapper(),
            http_client=http_client,
        )
        logger.debug("%s initialized.", type(self).__name__)

    @property
    def default_headers(self) -> dict[str, str]:
        """Headers sent with every request: the JSON representation."""
        return {"Accept": "application/json"}

    @cached_property
    def journals(self) -> JournalsClient:
        """The journals resource client."""
        return JournalsClient(self)

    @cached_property
    def articles(self) -> ArticlesClient:
        """The articles resource client."""
        return ArticlesClient(self)


__all__ = ["DiurnaliaClient", "DiurnaliaResourceClient"]
