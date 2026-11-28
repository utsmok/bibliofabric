"""Async ISSN Portal client; the single source of truth for the sync twin."""

import logging
from functools import cached_property

import httpx
from bibliofabric import BaseApiClient

from ..config import SeriatimSettings, get_settings
from ..unwrapper import SeriatimUnwrapper
from .ltwa import LtwaClient
from .resources import IssnLClient, RecordsClient
from .search import SearchClient

logger = logging.getLogger(__name__)


class SeriatimClient(BaseApiClient):
    """Client for the ISSN Portal (``https://portal.issn.org``).

    All wrapped routes are free and need no credentials. The client sends
    ``Accept: application/ld+json`` on every request; the record routes
    answer JSON-LD through content negotiation and the HTML routes (search,
    LTWA) answer HTML regardless, which their clients parse.
    """

    def __init__(
        self,
        settings: SeriatimSettings | None = None,
        *,
        base_url: str | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Build the client.

        Args:
            settings: Settings instance; ``None`` loads from the environment.
            base_url: Base URL override (testing).
            http_client: Optional pre-configured ``httpx.AsyncClient`` (caller
                retains ownership and is responsible for closing it).
        """
        super().__init__(
            base_url=base_url or "https://portal.issn.org",
            settings=settings or get_settings(),
            unwrapper=SeriatimUnwrapper(),
            http_client=http_client,
        )
        logger.debug("%s initialized.", type(self).__name__)

    @property
    def default_headers(self) -> dict[str, str]:
        """Headers sent with every request: the JSON-LD representation."""
        return {"Accept": "application/ld+json"}

    @cached_property
    def records(self) -> RecordsClient:
        """The ``/resource/ISSN`` record client."""
        return RecordsClient(self)

    @cached_property
    def issn_l(self) -> IssnLClient:
        """The ``/resource/ISSN-L`` cluster client."""
        return IssnLClient(self)

    @cached_property
    def search(self) -> SearchClient:
        """The free search over the HTML result page."""
        return SearchClient(self)

    @cached_property
    def ltwa(self) -> LtwaClient:
        """The list of Title Word Abbreviations."""
        return LtwaClient(self)


__all__ = ["SeriatimClient"]
