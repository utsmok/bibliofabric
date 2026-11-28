"""Async ROR v2 client; the single source of truth for the sync twin."""

import logging
from functools import cached_property
from typing import override

import httpx
from bibliofabric import BaseApiClient

from ..config import RoriferSettings, get_settings
from ..dialect import ROR_API_BASE_URL, ROR_HEARTBEAT_PATH, ROR_ZENODO_HOST
from ..unwrapper import RoriferUnwrapper
from .dumps import DumpsClient
from .organizations import OrganizationsClient

logger = logging.getLogger(__name__)


class RoriferClient(BaseApiClient):
    """Client for the ROR v2 API.

    The API needs no credentials. The client sends ``Accept: application/json``
    on every request; the API answers no other representation.
    """

    def __init__(
        self,
        settings: RoriferSettings | None = None,
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
            base_url=base_url or ROR_API_BASE_URL,
            settings=settings or get_settings(),
            unwrapper=RoriferUnwrapper(),
            http_client=http_client,
        )
        logger.debug("%s initialized.", type(self).__name__)

    @property
    def default_headers(self) -> dict[str, str]:
        """Headers sent with every request: the JSON representation."""
        return {"Accept": "application/json"}

    @override
    def rate_class(self, request: httpx.Request) -> str:
        """Pace requests to Zenodo in their own class.

        The anonymous Zenodo search accepts 30 requests per minute, far less
        than the ROR API, so the data dump helper gets the ``zenodo`` rate
        class of :attr:`RoriferSettings.rate_limits`.
        """
        return "zenodo" if request.url.host == ROR_ZENODO_HOST else "default"

    @cached_property
    def organizations(self) -> OrganizationsClient:
        """The organizations resource client."""
        return OrganizationsClient(self)

    @cached_property
    def dumps(self) -> DumpsClient:
        """The ROR data dumps hosted on Zenodo."""
        return DumpsClient(self)

    async def heartbeat(self) -> bool:
        """Return ``True`` when the ROR API answers its health check with ``OK``.

        The check calls ``GET /heartbeat`` on the host of the base URL,
        outside the ``v2`` prefix. An error status raises, as with every
        request.
        """
        url = httpx.URL(self.base_url).copy_with(path=ROR_HEARTBEAT_PATH)
        response = await self.request("GET", str(url))
        return response.text.strip() == "OK"


__all__ = ["RoriferClient"]
