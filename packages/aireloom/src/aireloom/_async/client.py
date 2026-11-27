"""The AIREloom client for the OpenAIRE Graph and Scholexplorer APIs."""

import functools
import logging
import warnings
from collections.abc import Mapping
from typing import Any

import httpx
from bibliofabric import BaseApiClient
from bibliofabric.auth import (
    AuthStrategy,
    ClientCredentialsAuth,
    NoAuth,
    RefreshTokenAuth,
)
from bibliofabric.exceptions import ConfigurationError

from ..config import AireloomSettings, get_settings
from ..unwrapper import OpenAireUnwrapper, ScholixUnwrapper
from .resources import (
    DataSourcesResource,
    LinksResource,
    OrganizationsResource,
    PersonsResource,
    ProjectsResource,
    ResearchProductsResource,
    ScholixResource,
)

logger = logging.getLogger(__name__)


def _resolve_auth(settings: AireloomSettings) -> AuthStrategy:
    """Resolve the auth strategy: refresh token, client credentials, or anonymous."""
    if settings.openaire_refresh_token:
        return RefreshTokenAuth(
            settings.token_url,
            settings.openaire_refresh_token,
            client_id=settings.openaire_client_id or None,
            client_secret=settings.openaire_client_secret or None,
            user_agent=settings.effective_user_agent(),
        )
    if settings.openaire_client_id and settings.openaire_client_secret:
        return ClientCredentialsAuth(
            settings.openaire_client_id,
            settings.openaire_client_secret,
            settings.token_url,
            user_agent=settings.effective_user_agent(),
        )
    if settings.openaire_client_id or settings.openaire_client_secret:
        raise ConfigurationError(
            "Both 'openaire_client_id' and 'openaire_client_secret' must be set "
            "together for OAuth2 client-credentials authentication."
        )
    return NoAuth()


class AireloomClient(BaseApiClient):
    """Client for the OpenAIRE Graph API (V4) and the Scholexplorer API.

    Entity resources are available as typed attributes; single-entity lookups
    go through the V3 by-id routes because V4 has none. Authentication
    resolves in the constructor: set ``openaire_refresh_token`` /
    ``refresh_token`` for OAuth2 refresh-token access, or set both
    ``openaire_client_id`` and ``openaire_client_secret`` (settings,
    ``AIRELOOM_OPENAIRE_CLIENT_ID`` / ``AIRELOOM_OPENAIRE_CLIENT_SECRET``, or
    ``client_id`` / ``client_secret``) for OAuth2 client-credentials access
    against the Keycloak token endpoint; partial client credentials raise
    :class:`ConfigurationError`, and without credentials the client is
    anonymous. An explicit ``auth_strategy`` always wins.

    The Scholix resource talks to the Scholexplorer host through a second
    internal client that shares settings and credentials but throttles itself
    to one request per second. See the package README and docs for usage
    examples of both the async and the sync variants.
    """

    def __init__(
        self,
        settings: AireloomSettings | None = None,
        auth: AuthStrategy | None = None,
        *,
        auth_strategy: AuthStrategy | None = None,
        base_url: str | None = None,
        scholix_base_url: str | None = None,
        mailto: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        refresh_token: str | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Build the client from settings, resolving credentials immediately.

        ``settings`` defaults to :func:`aireloom.config.get_settings`, which
        reads ``AIRELOOM_*`` environment variables and ``.env``. Keyword
        overrides (``base_url``, ``scholix_base_url``, ``mailto``,
        ``client_id``, ``client_secret``, ``refresh_token``) take precedence
        over ``settings``. Pass ``auth_strategy`` for a custom auth strategy
        (``auth`` is a deprecated alias).
        """
        if auth is not None and auth_strategy is not None:
            raise ConfigurationError(
                "Pass either 'auth_strategy' or the deprecated 'auth' parameter, "
                "not both."
            )
        if auth is not None:
            warnings.warn(
                "The 'auth' parameter is deprecated; use 'auth_strategy' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            explicit_auth: AuthStrategy | None = auth
        else:
            explicit_auth = auth_strategy

        resolved = settings or get_settings()
        overrides: dict[str, str] = {}
        if base_url is not None:
            overrides["base_url"] = base_url
        if scholix_base_url is not None:
            overrides["scholix_base_url"] = scholix_base_url
        if mailto is not None:
            overrides["mailto"] = mailto
        if client_id is not None:
            overrides["openaire_client_id"] = client_id
        if client_secret is not None:
            overrides["openaire_client_secret"] = client_secret
        if refresh_token is not None:
            overrides["openaire_refresh_token"] = refresh_token
        if overrides:
            resolved = resolved.model_copy(update=overrides)
        strategy = (
            explicit_auth if explicit_auth is not None else _resolve_auth(resolved)
        )
        super().__init__(
            base_url=resolved.base_url,
            settings=resolved,
            unwrapper=OpenAireUnwrapper(),
            auth=strategy,
            http_client=http_client,
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
        auth_label = (
            "anonymous" if isinstance(strategy, NoAuth) else type(strategy).__name__
        )
        logger.debug("%s initialized (%s).", type(self).__name__, auth_label)

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        data: Mapping[str, Any] | None = None,
        content: str | bytes | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float | httpx.Timeout | None = None,
        retry: bool | None = None,
    ) -> httpx.Response:
        """Send a request through the core retry pipeline.

        V4 accepts ``mailto`` for polite-pool admission (V3 rejects it), so the
        configured contact address is attached to ``v4/`` requests only.
        """
        effective_params: Mapping[str, Any] | None = params
        if path.lstrip("/").startswith("v4/") and self._settings.mailto:
            if params is None:
                effective_params = {"mailto": self._settings.mailto}
            elif isinstance(params, Mapping):
                if "mailto" not in params:
                    effective_params = {"mailto": self._settings.mailto, **params}
            else:
                qp = httpx.QueryParams(params)
                if "mailto" not in qp:
                    effective_params = qp.set("mailto", self._settings.mailto)
        return await super().request(
            method,
            path,
            params=effective_params,
            json=json,
            data=data,
            content=content,
            headers=headers,
            timeout=timeout,
            retry=retry,
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
        """Search Scholix links on the Scholexplorer host (V3, V2 for linkProvider)."""
        return ScholixResource(self._scholix_api)

    async def aclose(self) -> None:
        """Close both the Graph and the Scholix HTTP clients."""
        try:
            await super().aclose()
        finally:
            await self._scholix_api.aclose()
