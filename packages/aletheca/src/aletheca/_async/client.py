"""The OpenAlex API clients.

``AlethecaClient`` owns settings resolution, auth-scheme selection, the
keyless-401 explanation, and the daily-budget 429 veto. ``scripts/unasync.py``
generates the sync twin ``AlethecaSyncClient`` from this module."""

import logging
from collections.abc import Mapping
from functools import cached_property
from typing import Any

import httpx
from bibliofabric import BaseApiClient, validate_model
from bibliofabric.auth import (
    AuthStrategy,
    NoAuth,
    QueryParameterAuth,
    StaticTokenAuth,
)
from bibliofabric.exceptions import AuthError, ConfigurationError
from pydantic import BaseModel

from ..config import AlethecaSettings, AuthScheme, get_settings
from ..dialect import AUTOCOMPLETE_ENTITY_TYPES, OPENALEX_API_BASE_URL
from ..models import AutocompleteResult, RateLimitStatus
from ..unwrapper import OpenAlexUnwrapper
from .authors import AuthorsClient
from .awards import AwardsClient
from .dialect import serialize_filter_params
from .funders import FundersClient
from .institutions import InstitutionsClient
from .keywords import KeywordsClient
from .links import LinksClient
from .locations import LocationsClient
from .publishers import PublishersClient
from .sources import SourcesClient
from .topics import TopicsClient
from .works import WorksClient

logger = logging.getLogger(__name__)

_UNAUTHORIZED = 401
_TOO_MANY_REQUESTS = 429
_VALID_AUTH_SCHEMES = frozenset({"query", "bearer"})


class AlethecaClient(BaseApiClient):
    """Client for the OpenAlex API.

    Credentials resolve in the constructor: an explicit ``api_key`` argument
    wins, then :class:`AlethecaSettings` (``ALETHECA_API_KEY`` or the
    consumer-legacy ``ALETHECA_OPENALEX_API_KEY`` env name). Without a key
    the client shares OpenAlex's $0.10/day per-IP budget and cannot use
    cursor paging past the first page; a free key fixes both. Usage examples
    live in the README and the documentation quick start.
    """

    def __init__(
        self,
        settings: AlethecaSettings | None = None,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        auth_strategy: AuthStrategy | None = None,
        auth_scheme: AuthScheme | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Build the client.

        Args:
            settings: Settings instance; ``None`` loads from the environment.
            api_key: OpenAlex API key; overrides the settings value. Pass
                ``""`` to force keyless access even when an env key is set.
            base_url: API base URL override (testing).
            auth_strategy: Fully custom auth strategy; takes precedence over
                ``api_key``/``auth_scheme``.
            auth_scheme: ``"query"`` (default, ``?api_key=``) or ``"bearer"``
                (``Authorization: Bearer``); overrides the settings value.
            http_client: Optional pre-configured ``httpx.AsyncClient`` (caller
                retains ownership and is responsible for closing it).
        """
        resolved_settings = settings or get_settings()
        raw_key = resolved_settings.api_key if api_key is None else api_key
        key = raw_key or None
        scheme = resolved_settings.auth_scheme if auth_scheme is None else auth_scheme
        if auth_strategy is not None:
            auth = auth_strategy
            keyless = isinstance(auth, NoAuth)
        else:
            if scheme not in _VALID_AUTH_SCHEMES:
                raise ConfigurationError(
                    f"auth_scheme must be 'query' or 'bearer', got {scheme!r}."
                )
            auth = self._resolve_auth(key, scheme)
            keyless = not key
        self._keyless = keyless
        self._last_rate_limit_headers: dict[str, str] = {}
        super().__init__(
            base_url=base_url or OPENALEX_API_BASE_URL,
            settings=resolved_settings,
            unwrapper=OpenAlexUnwrapper(),
            auth=auth,
            http_client=http_client,
        )
        logger.debug("%s initialized (keyless=%s).", type(self).__name__, keyless)

    @property
    def last_rate_limit_headers(self) -> dict[str, str]:
        """Return ``x-ratelimit-*`` headers captured from the most recent response."""
        return dict(self._last_rate_limit_headers)

    def on_response(self, response: httpx.Response) -> None:
        """Capture OpenAlex ``x-ratelimit-*`` headers from the latest response."""
        self._last_rate_limit_headers = {
            key.lower(): value
            for key, value in response.headers.items()
            if key.lower().startswith("x-ratelimit-")
        }

    @staticmethod
    def _resolve_auth(api_key: str | None, scheme: AuthScheme) -> AuthStrategy:
        """Pick the auth strategy for a key and scheme."""
        if not api_key:
            return NoAuth()
        if scheme == "bearer":
            return StaticTokenAuth(api_key)
        return QueryParameterAuth("api_key", api_key)

    def rate_class(self, request: httpx.Request) -> str:
        """Route ``search.semantic`` requests to the 1 req/s ``semantic`` class."""
        if "search.semantic" in request.url.params:
            return "semantic"
        return "default"

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
        """Send a request with retries, mapping keyless 401s to clear errors.

        OpenAlex 401s most often mean cursor paging without an API key; the
        re-raised message says how to fix it (OX-02).
        """
        try:
            return await super().request(
                method,
                path,
                params=params,
                json=json,
                data=data,
                content=content,
                headers=headers,
                timeout=timeout,
                retry=retry,
            )
        except AuthError as error:
            response = error.response
            if (
                self._keyless
                and response is not None
                and response.status_code == _UNAUTHORIZED
            ):
                raise AuthError(
                    "OpenAlex rejected this request with 401. Keyless access "
                    "cannot use cursor paging past the first page and shares "
                    "a small daily budget per IP address. Get a free API key "
                    "at https://openalex.org/settings/api and set "
                    "ALETHECA_API_KEY (or pass api_key= to "
                    f"{type(self).__name__}).",
                    body=error.body,
                    request=error.request,
                    response=response,
                ) from error
            raise

    def is_retryable(self, response: httpx.Response) -> bool:
        """Veto retries for 429s whose ``reason`` is ``daily_budget``.

        A daily-budget 429 will not succeed before the UTC midnight reset,
        so retrying only burns the caller's remaining budget (OX-15).
        """
        if response.status_code == _TOO_MANY_REQUESTS:
            try:
                body = response.json()
            except Exception:  # any body parse failure retries normally
                body = None
            if isinstance(body, dict) and body.get("reason") == "daily_budget":
                return False
        return super().is_retryable(response)

    # --- non-entity endpoints ------------------------------------------

    async def autocomplete(
        self,
        query: str,
        *,
        entity_type: str | None = None,
        filters: BaseModel | Mapping[str, Any] | None = None,
    ) -> list[AutocompleteResult]:
        """Free typeahead/ID resolution; returns up to 10 rows per call.

        ``entity_type`` restricts to one autocomplete route (``"works"``,
        ``"authors"``, ``"institutions"``, ``"sources"``, ``"topics"``,
        ``"keywords"``, ``"concepts"``, ``"publishers"``, or ``"funders"``;
        OpenAlex does not provide ``/autocomplete/awards``). Optional
        ``filters`` narrows candidates using OpenAlex filter syntax. Costs no
        credits.
        """
        if entity_type is not None and entity_type not in AUTOCOMPLETE_ENTITY_TYPES:
            raise ConfigurationError(
                f"entity_type must be one of {sorted(AUTOCOMPLETE_ENTITY_TYPES)}, "
                f"got {entity_type!r}."
            )
        path = "autocomplete" if entity_type is None else f"autocomplete/{entity_type}"
        params: dict[str, str] = {"q": query}
        params.update(serialize_filter_params(filters))
        response = await self.request("GET", path, params=params)
        body = self.parse_json(response)
        rows = body.get("results") if isinstance(body, dict) else None
        return [
            validate_model(
                AutocompleteResult,
                row,
                request=response.request,
                response=response,
            )
            for row in rows or []
        ]

    async def rate_limit(self) -> RateLimitStatus:
        """Return the key's remaining daily budget and per-second caps.

        Free, costs no credits; useful as a guard before large jobs.
        """
        response = await self.request("GET", "rate-limit")
        body = self.parse_json(response)
        return validate_model(
            RateLimitStatus,
            body,
            request=response.request,
            response=response,
        )

    # --- entity resources -----------------------------------------------

    @cached_property
    def works(self) -> WorksClient:
        """The works resource client."""
        return WorksClient(self)

    @cached_property
    def authors(self) -> AuthorsClient:
        """The authors resource client."""
        return AuthorsClient(self)

    @cached_property
    def sources(self) -> SourcesClient:
        """The sources resource client."""
        return SourcesClient(self)

    @cached_property
    def institutions(self) -> InstitutionsClient:
        """The institutions resource client."""
        return InstitutionsClient(self)

    @cached_property
    def topics(self) -> TopicsClient:
        """The topics resource client."""
        return TopicsClient(self)

    @cached_property
    def keywords(self) -> KeywordsClient:
        """The keywords resource client."""
        return KeywordsClient(self)

    @cached_property
    def publishers(self) -> PublishersClient:
        """The publishers resource client."""
        return PublishersClient(self)

    @cached_property
    def funders(self) -> FundersClient:
        """The funders resource client."""
        return FundersClient(self)

    @cached_property
    def awards(self) -> AwardsClient:
        """The awards resource client."""
        return AwardsClient(self)

    @cached_property
    def locations(self) -> LocationsClient:
        """The locations resource client (the per-copy index)."""
        return LocationsClient(self)

    @cached_property
    def links(self) -> LinksClient:
        """The links resource client (typed one-hop work edges)."""
        return LinksClient(self)
