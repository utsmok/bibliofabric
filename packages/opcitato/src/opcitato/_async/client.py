"""Async OpenCitations client; the single source of truth for the sync twin."""

import logging
from functools import cached_property

import httpx
from bibliofabric import BaseApiClient

from ..config import OpcitatoSettings, get_settings
from ..dialect import OPENCITATIONS_API_BASE_URL
from ..unwrapper import OpcitatoUnwrapper
from .resources import IndexClient, MetaClient

logger = logging.getLogger(__name__)


class OpcitatoClient(BaseApiClient):
    """Client for the OpenCitations Index API v2 and Meta API v1.

    The APIs need no credentials; anonymous usage is rate-limited to 180
    requests per minute per IP address, which the settings pace to
    3 requests per second. OpenCitations sells Access Tokens that raise the
    limit; such a token would travel in an ``authorization`` header and can
    be added through ``default_headers`` once credentials exist. The client
    sends ``Accept: application/json`` on every request; ``format="csv"``
    selects the CSV representation regardless of that header.
    """

    def __init__(
        self,
        settings: OpcitatoSettings | None = None,
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
            base_url=base_url or OPENCITATIONS_API_BASE_URL,
            settings=settings or get_settings(),
            unwrapper=OpcitatoUnwrapper(),
            http_client=http_client,
        )
        logger.debug("%s initialized.", type(self).__name__)

    @property
    def default_headers(self) -> dict[str, str]:
        """Headers sent with every request: the JSON representation."""
        return {"Accept": "application/json"}

    @cached_property
    def index(self) -> IndexClient:
        """The Index API resource client (citations, references, counts)."""
        return IndexClient(self)

    @cached_property
    def meta(self) -> MetaClient:
        """The Meta API resource client (metadata, authors, editors)."""
        return MetaClient(self)


__all__ = ["OpcitatoClient"]
