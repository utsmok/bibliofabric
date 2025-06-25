from typing import Self

from bibliofabric.auth import (
    AuthStrategy,
    ClientCredentialsAuth,
    NoAuth,
    StaticTokenAuth,
)
from bibliofabric.client import BaseApiClient
from bibliofabric.log_config import logger

from .config import ApiSettings, get_settings
from .constants import (
    OPENAIRE_GRAPH_API_BASE_URL,
    OPENAIRE_SCHOLIX_API_BASE_URL,
)
from .resources import (
    DataSourcesClient,
    OrganizationsClient,
    ProjectsClient,
    ResearchProductsClient,
    ScholixClient,
)
from .unwrapper import OpenAireUnwrapper


class AireloomClient(BaseApiClient):
    """Asynchronous HTTP client for interacting with OpenAIRE APIs.

    This client inherits all generic HTTP functionality from BaseApiClient
    and adds OpenAIRE-specific resource clients and configuration.
    """

    def __init__(
        self,
        settings: ApiSettings | None = None,
        auth_strategy: AuthStrategy | None = None,
        *,
        # Allow direct override for testing/specific cases, but prefer settings
        api_token: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        base_url: str = OPENAIRE_GRAPH_API_BASE_URL,
        scholix_base_url: str = OPENAIRE_SCHOLIX_API_BASE_URL,
    ):
        """
        Initializes the AireloomClient with OpenAIRE-specific functionality.

        Authentication is determined automatically based on settings unless an
        explicit `auth_strategy` is provided.

        Order of precedence for automatic auth determination:
        1. Client Credentials (if client_id & client_secret are configured)
        2. Static Token (if api_token is configured)
        3. No Authentication

        Args:
            settings: Optional ApiSettings instance. If None, loads global settings.
            auth_strategy: Optional explicit authentication strategy instance.
            api_token: Optional static API token (overrides settings if provided).
            client_id: Optional client ID (overrides settings if provided).
            client_secret: Optional client secret (overrides settings if provided).
            base_url: The base URL for the OpenAIRE Graph API.
            scholix_base_url: The base URL for the OpenAIRE Scholix API.
        """
        self._settings = settings or get_settings()
        self._scholix_base_url = scholix_base_url.rstrip("/")

        logger.debug(
            f"AireloomClient.__init__ settings: id={id(self._settings)}, "
            f"client_id={self._settings.openaire_client_id}, "
            f"token={self._settings.openaire_api_token}, "
            f"timeout={self._settings.request_timeout}"
        )

        # Determine authentication strategy if not explicitly provided
        if auth_strategy:
            logger.info(
                f"Using explicitly provided authentication strategy: {type(auth_strategy).__name__}"
            )
            resolved_auth_strategy = auth_strategy
        else:
            logger.info(
                "Determining auth type based on provided parameters or settings."
            )
            # Use overrides if provided, otherwise use settings
            _client_id = client_id or self._settings.openaire_client_id
            _client_secret = client_secret or self._settings.openaire_client_secret
            _api_token = api_token or self._settings.openaire_api_token
            _token_url = self._settings.openaire_token_url

            logger.debug(
                f"Auth decision: client_id_param={client_id}, "
                f"settings_client_id={self._settings.openaire_client_id}, "
                f"api_token_param={api_token}, "
                f"settings_api_token={self._settings.openaire_api_token}"
            )

            if _client_id and _client_secret:
                logger.info("Using Client Credentials authentication.")
                if client_id and client_secret:
                    logger.info(
                        "Client ID and secret were directly passed as parameters."
                    )
                else:
                    logger.info(
                        "Client ID and secret were loaded from settings or environment variables."
                    )
                resolved_auth_strategy = ClientCredentialsAuth(
                    client_id=_client_id,
                    client_secret=_client_secret,
                    token_url=_token_url,
                )
            elif _api_token:
                logger.info("Using Static Token authentication.")
                resolved_auth_strategy = StaticTokenAuth(token=_api_token)
            else:
                logger.info("No authentication credentials found, using NoAuth.")
                resolved_auth_strategy = NoAuth()

        # Create the OpenAIRE response unwrapper
        unwrapper = OpenAireUnwrapper()

        # Initialize the base client with all the generic functionality
        super().__init__(
            base_url=base_url,
            settings=self._settings,
            auth_strategy=resolved_auth_strategy,
            response_unwrapper=unwrapper,
        )

        # Initialize OpenAIRE-specific resource clients
        self._research_products = ResearchProductsClient(api_client=self)
        self._organizations = OrganizationsClient(api_client=self)
        self._projects = ProjectsClient(api_client=self)
        self._data_sources = DataSourcesClient(api_client=self)
        self._scholix = ScholixClient(
            api_client=self, scholix_base_url=self._scholix_base_url
        )

        logger.debug("AireloomClient initialized successfully.")

    @property
    def research_products(self) -> ResearchProductsClient:
        """Access ResearchProductsClient."""
        return self._research_products

    @property
    def organizations(self) -> OrganizationsClient:
        """Access OrganizationsClient."""
        return self._organizations

    @property
    def projects(self) -> ProjectsClient:
        """Access ProjectsClient."""
        return self._projects

    @property
    def data_sources(self) -> DataSourcesClient:
        """Access DataSourcesClient."""
        return self._data_sources

    @property
    def scholix(self) -> ScholixClient:
        """Access ScholixClient."""
        return self._scholix

    async def __aenter__(self) -> Self:
        """Async context manager entry."""
        logger.info(
            f"AireloomClient.__aenter__() called. Client ID: {id(self)}. "
            f"HTTP client closed: {self._http_client.is_closed if self._http_client else 'N/A'}"
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        logger.info(
            f"AireloomClient.__aexit__() called. Client ID: {id(self)}. "
            f"HTTP client closed before aclose: {self._http_client.is_closed if self._http_client else 'N/A'}"
        )
        await self.aclose()
        logger.info(
            f"AireloomClient.__aexit__() finished. Client ID: {id(self)}. "
            f"HTTP client closed after aclose: {self._http_client.is_closed if self._http_client else 'N/A'}"
        )
