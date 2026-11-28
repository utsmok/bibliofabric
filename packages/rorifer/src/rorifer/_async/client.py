"""Async ROR v2 client; the single source of truth for the sync twin."""

import logging
from functools import cached_property

import httpx
from bibliofabric import BaseApiClient

from ..config import RoriferSettings, get_settings
from ..dialect import ROR_API_BASE_URL
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

    @cached_property
    def organizations(self) -> OrganizationsClient:
        """The organizations resource client."""
        return OrganizationsClient(self)

    @cached_property
    def dumps(self) -> DumpsClient:
        """The ROR data dumps hosted on Zenodo."""
        return DumpsClient(self)


__all__ = ["RoriferClient"]
