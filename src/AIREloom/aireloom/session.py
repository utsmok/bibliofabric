"""Main user-facing session class for interacting with the OpenAIRE Graph API and Scholexplorer."""

from bibliofabric.auth import AuthStrategy
from bibliofabric.log_config import configure_logging, logger

from .client import AireloomClient
from .config import ApiSettings, get_settings  # Added ApiSettings
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

configure_logging()

# RESOURCE_CLIENTS_MAP is no longer needed as AireloomClient manages its own instances.


class AireloomSession:
    """Acts as a facade, providing access to OpenAIRE Graph API and Scholexplorer API
    resource clients managed by an underlying AireloomClient instance.
    """

    def __init__(
        self,
        auth_strategy: AuthStrategy | None = None,
        timeout: int
        | None = None,  # Overrides default request timeout for this session.
        api_base_url: str | None = None,
        scholix_base_url: str | None = None,
    ):
        """Initializes the Aireloom session and its underlying API client.

        Args:
            auth_strategy:  Authentication strategy (e.g., NoAuth(), TokenAuth(...)).
                            Defaults to NoAuth.
            timeout: Overrides the default request timeout (from settings)
                     for HTTP requests made through this session.
            api_base_url: Base URL for the OpenAIRE Graph API.
            scholix_base_url: Base URL for the Scholexplorer API.
        """
        # self._auth_strategy = auth_strategy or NoAuth() # Client will handle defaulting
        _api_base_url = api_base_url or OPENAIRE_GRAPH_API_BASE_URL
        _scholix_base_url = scholix_base_url or OPENAIRE_SCHOLIX_API_BASE_URL

        current_settings = get_settings()
        session_specific_settings: ApiSettings
        if timeout is not None:
            logger.debug(f"Overriding request timeout for this session to: {timeout}s")
            session_specific_settings = current_settings.model_copy(
                update={"request_timeout": timeout}
            )
        else:
            session_specific_settings = current_settings

        # Pass the original auth_strategy (which can be None) to the client.
        # The client will then decide its auth based on this and its settings.
        logger.debug(
            f"AireloomSession: Initializing AireloomClient with auth_strategy param: {type(auth_strategy)}"
        )
        self._api_client = AireloomClient(
            settings=session_specific_settings,
            auth_strategy=auth_strategy,  # Pass the original auth_strategy parameter
            base_url=_api_base_url,  # Pass Graph API base URL
            scholix_base_url=_scholix_base_url,  # Pass Scholix base URL
        )
        logger.info(f"AireloomSession initialized for API: {_api_base_url}")
        logger.info(f"Scholexplorer base URL configured for: {_scholix_base_url}")

    @property
    def research_products(self) -> ResearchProductsClient:
        """Access the ResearchProductsClient."""
        return self._api_client.research_products

    @property
    def organizations(self) -> OrganizationsClient:
        """Access the OrganizationsClient."""
        return self._api_client.organizations

    @property
    def projects(self) -> ProjectsClient:
        """Access the ProjectsClient."""
        return self._api_client.projects

    @property
    def data_sources(self) -> DataSourcesClient:
        """Access the DataSourcesClient."""
        return self._api_client.data_sources

    @property
    def scholix(self) -> ScholixClient:
        """Access the ScholixClient."""
        return self._api_client.scholix

    async def close(self) -> None:
        """Closes the underlying HTTP client session."""
        await self._api_client.aclose()

    async def __aenter__(self) -> "AireloomSession":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
