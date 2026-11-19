"""The AIREloom client for the OpenAIRE Graph and Scholexplorer APIs."""

import functools
import logging
from typing import Any

import httpx
from bibliofabric import BaseApiClient
from bibliofabric.auth import AuthStrategy, ClientCredentialsAuth, NoAuth

from .config import AireloomSettings, get_settings
from .resources import (
    DataSourcesResource,
    LinksResource,
    OrganizationsResource,
    PersonsResource,
    ProjectsResource,
    ResearchProductsResource,
    ScholixResource,
)
from .unwrapper import OpenAireUnwrapper, ScholixUnwrapper

logger = logging.getLogger(__name__)


def _resolve_auth(settings: AireloomSettings) -> AuthStrategy:
    """Resolve the auth strategy: client credentials, else anonymous."""
    if settings.openaire_client_id and settings.openaire_client_secret:
        return ClientCredentialsAuth(
            settings.openaire_client_id,
            settings.openaire_client_secret,
            settings.token_url,
            user_agent=settings.effective_user_agent(),
        )
    return NoAuth()


class AireloomClient(BaseApiClient):
    """Async client for the OpenAIRE Graph API (V4) and the Scholexplorer API.

    Entity resources are available as typed attributes; single-entity lookups
    go through the V3 by-id routes because V4 has none. Authentication
    resolves in the constructor: set ``openaire_client_id`` and
    ``openaire_client_secret`` (settings or ``AIRELOOM_OPENAIRE_CLIENT_ID`` /
    ``AIRELOOM_OPENAIRE_CLIENT_SECRET``) for OAuth2 client-credentials access
    against the Keycloak token endpoint; without credentials the client is
    anonymous. An explicit ``auth`` strategy always wins.

    The Scholix resource talks to the Scholexplorer host through a second
    internal client that shares settings and credentials but throttles itself
    to one request per second.

    Example:
        ```python
        async with AireloomClient() as client:
            product = await client.research_products.get(
                "doi_dedup___::abc123"
            )
            async for project in client.projects.iterate():
                print(project.title)
        ```
    """

    def __init__(
        self,
        settings: AireloomSettings | None = None,
        auth: AuthStrategy | None = None,
        *,
        base_url: str | None = None,
        scholix_base_url: str | None = None,
    ) -> None:
        """Build the client from settings, resolving credentials immediately.

        ``settings`` defaults to :func:`aireloom.config.get_settings`, which
        reads ``AIRELOOM_*`` environment variables and ``.env``. The ``base_url``
        and ``scholix_base_url`` arguments override the settings values.
        """
        resolved = settings or get_settings()
        overrides: dict[str, str] = {}
        if base_url is not None:
            overrides["base_url"] = base_url
        if scholix_base_url is not None:
            overrides["scholix_base_url"] = scholix_base_url
        if overrides:
            resolved = resolved.model_copy(update=overrides)
        strategy = auth if auth is not None else _resolve_auth(resolved)
        super().__init__(
            base_url=resolved.base_url,
            settings=resolved,
            unwrapper=OpenAireUnwrapper(),
            auth=strategy,
        )
        self._scholix_api = BaseApiClient(
            base_url=resolved.scholix_base_url,
            settings=resolved.model_copy(
                update={
                    "max_requests_per_second": resolved.scholix_max_requests_per_second
                }
            ),
            unwrapper=ScholixUnwrapper(),
            auth=strategy,
        )
        logger.debug(
            "AireloomClient initialized (%s).",
            "anonymous" if isinstance(strategy, NoAuth) else "client credentials",
        )

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Any | None = None,
        json: Any | None = None,
        headers: Any | None = None,
    ) -> httpx.Response:
        """Send a request through the core retry pipeline.

        V4 accepts ``mailto`` for polite-pool admission (V3 rejects it), so the
        configured contact address is attached to ``v4/`` requests only.
        """
        if (
            path.startswith("v4/")
            and self._settings.mailto
            and not (params and "mailto" in params)
        ):
            params = {"mailto": self._settings.mailto, **(params or {})}
        return await super().request(
            method, path, params=params, json=json, headers=headers
        )

    @functools.cached_property
    def _links(self) -> LinksResource:
        return LinksResource(self)

    @functools.cached_property
    def research_products(self) -> ResearchProductsResource:
        """Search, iterate, and batch-fetch research products; links helpers."""
        return ResearchProductsResource(self, self._links)

    @functools.cached_property
    def projects(self) -> ProjectsResource:
        """Search and iterate OpenAIRE projects."""
        return ProjectsResource(self)

    @functools.cached_property
    def organizations(self) -> OrganizationsResource:
        """Search and iterate OpenAIRE organizations."""
        return OrganizationsResource(self)

    @functools.cached_property
    def data_sources(self) -> DataSourcesResource:
        """Search and iterate OpenAIRE data sources."""
        return DataSourcesResource(self)

    @functools.cached_property
    def persons(self) -> PersonsResource:
        """Search and iterate OpenAIRE persons."""
        return PersonsResource(self)

    @functools.cached_property
    def scholix(self) -> ScholixResource:
        """Search Scholix links on the Scholexplorer host (V3, V2 for dates)."""
        return ScholixResource(self._scholix_api)

    async def aclose(self) -> None:
        """Close both the Graph and the Scholix HTTP clients."""
        await super().aclose()
        await self._scholix_api.aclose()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        await self.aclose()
