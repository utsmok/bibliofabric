"""StavrophoraClient — async client for the Crossref API."""

import re
from functools import cached_property

import httpx
from bibliofabric import BaseApiClient
from bibliofabric.auth import AuthStrategy, HeaderAuth, NoAuth, QueryParameterAuth

from .config import StavrophoraSettings, get_settings
from .resources.funders import FundersResource
from .resources.journals import JournalsResource
from .resources.licenses import LicensesResource
from .resources.members import MembersResource
from .resources.prefixes import PrefixesResource
from .resources.types import TypesResource
from .resources.works import WorksResource
from .unwrapper import CrossrefUnwrapper

#: Documented canonical base for the Crossref REST API.
CROSSREF_API_BASE_URL = "https://api.crossref.org/v1"

#: Metadata Plus authentication header (the old ``Crossref-Plus-API-Token``
#: name is no longer documented).
PLUS_TOKEN_HEADER = "crossref-api-key"


class StavrophoraClient(BaseApiClient):
    """Asynchronous client for the Crossref API.

    Usage::

        async with StavrophoraClient(
            mailto="you@example.org"
        ) as client:
            work = await client.works.get("10.1038/nature12373")
            page = await client.works.search(
                query="proteomics", select=["DOI", "title"]
            )
            async for work in client.works.iterate():
                ...

    Credentials are resolved in the constructor: an explicit ``auth_strategy``
    wins, then a Metadata Plus key (``crossref-api-key`` header), then
    ``mailto`` (polite pool via query parameter). The settings pace per
    request class (D-19): top-level ``/works`` searches at 3 requests/s and
    everything else (single records, scoped ``/.../works`` routes, all other
    routes) at 10 requests/s, with 3 concurrent requests shared across
    classes.
    """

    def __init__(
        self,
        settings: StavrophoraSettings | None = None,
        *,
        mailto: str | None = None,
        plus_token: str | None = None,
        base_url: str | None = None,
        auth_strategy: AuthStrategy | None = None,
    ) -> None:
        resolved = settings or get_settings()
        mailto = mailto or resolved.mailto
        plus_token = plus_token or resolved.plus_token
        if auth_strategy is not None:
            auth = auth_strategy
        elif plus_token:
            auth = HeaderAuth(PLUS_TOKEN_HEADER, f"Bearer {plus_token}")
        elif mailto:
            auth = QueryParameterAuth("mailto", mailto)
        else:
            auth = NoAuth()
        super().__init__(
            base_url=base_url or CROSSREF_API_BASE_URL,
            settings=resolved,
            unwrapper=CrossrefUnwrapper(),
            auth=auth,
        )

    @cached_property
    def works(self) -> WorksResource:
        """The ``/works`` resource (search, iterate, batch DOI lookup, agency)."""
        return WorksResource(self)

    @cached_property
    def journals(self) -> JournalsResource:
        """The ``/journals`` resource."""
        return JournalsResource(self)

    @cached_property
    def funders(self) -> FundersResource:
        """The ``/funders`` resource."""
        return FundersResource(self)

    @cached_property
    def members(self) -> MembersResource:
        """The ``/members`` resource."""
        return MembersResource(self)

    @cached_property
    def types(self) -> TypesResource:
        """The ``/types`` resource."""
        return TypesResource(self)

    @cached_property
    def prefixes(self) -> PrefixesResource:
        """The ``/prefixes`` resource."""
        return PrefixesResource(self)

    @cached_property
    def licenses(self) -> LicensesResource:
        """The ``/licenses`` resource (list/iterate only)."""
        return LicensesResource(self)

    #: Only the top-level ``/works`` route is array-class. Everything else —
    #: single records, scoped ``/.../works`` routes, and all other routes —
    #: reports the ``polite-single`` pool in Crossref's ``x-api-pool`` header
    #: (2026-07-21 rate split; see the README and the phase 2 research).
    _TOP_LEVEL_WORKS = re.compile(r"/v1/works$")

    def rate_class(self, request: httpx.Request) -> str:
        """Map the request onto Crossref's polite pools (D-19)."""
        if self._TOP_LEVEL_WORKS.search(request.url.path):
            return "list"
        return "single"
