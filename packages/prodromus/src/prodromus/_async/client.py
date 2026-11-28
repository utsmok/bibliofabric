"""Async bioRxiv and medRxiv client; the single source of truth for the sync twin."""

import logging
from functools import cached_property

import httpx
from bibliofabric import BaseApiClient

from ..config import ProdromusSettings, get_settings
from ..dialect import BIORXIV_API_BASE_URL
from ..unwrapper import ProdromusUnwrapper
from .routes import DetailsClient, FundersClient, PublishedClient, StatisticsClient

logger = logging.getLogger(__name__)


class ProdromusClient(BaseApiClient):
    """Client for the bioRxiv and medRxiv API (``https://api.biorxiv.org``).

    One client serves both preprint servers; most methods take ``server``
    (``biorxiv`` or ``medrxiv``). The API needs no credentials.
    """

    def __init__(
        self,
        settings: ProdromusSettings | None = None,
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
            base_url=base_url or BIORXIV_API_BASE_URL,
            settings=settings or get_settings(),
            unwrapper=ProdromusUnwrapper(),
            http_client=http_client,
        )
        logger.debug("%s initialized.", type(self).__name__)

    @property
    def default_headers(self) -> dict[str, str]:
        """Headers sent with every request: the JSON representation."""
        return {"Accept": "application/json"}

    @cached_property
    def details(self) -> DetailsClient:
        """Preprint metadata: by DOI, by date range, and the newest posts."""
        return DetailsClient(self)

    @cached_property
    def published(self) -> PublishedClient:
        """Links from preprints to the journal articles they became."""
        return PublishedClient(self)

    @cached_property
    def funders(self) -> FundersClient:
        """Preprints filtered by a funder ROR id."""
        return FundersClient(self)

    @cached_property
    def statistics(self) -> StatisticsClient:
        """Content and usage statistics."""
        return StatisticsClient(self)


__all__ = ["ProdromusClient"]
