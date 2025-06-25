# aireloom/config.py
from functools import lru_cache

from bibliofabric.config import BaseApiSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict

# Import OpenAIRE-specific constants
from .constants import DEFAULT_USER_AGENT, REGISTERED_SERVICE_API_TOKEN_URL


class ApiSettings(BaseApiSettings):
    """
    OpenAIRE-specific settings for the AIREloom client.

    Inherits all generic API client settings from BaseApiSettings and adds
    OpenAIRE-specific authentication and configuration fields.

    Settings are loaded from environment variables (prefixed with 'AIRELOOM_')
    or .env/secrets.env files.
    """

    model_config = SettingsConfigDict(
        env_file=(".env", "secrets.env"),  # Look in both .env and secrets.env
        env_file_encoding="utf-8",
        # Environment variables should be prefixed, e.g., AIRELOOM_OPENAIRE_API_TOKEN
        env_prefix="AIRELOOM_",
        extra="ignore",  # Ignore extra fields found in environment
        case_sensitive=False,  # Allow AIRELOOM_openaire_api_token etc.
        arbitrary_types_allowed=True,  # Required for hook callables
    )

    # Override the default user agent to use OpenAIRE-specific value
    user_agent: str = Field(
        default=DEFAULT_USER_AGENT,
        description="User-Agent header for requests",
    )

    # --- OpenAIRE-specific Authentication Settings ---
    # Option 1: Static API Token
    openaire_api_token: str | None = Field(
        default=None, description="Static OpenAIRE API Token (optional)"
    )

    # Option 2: Client Credentials for OAuth2 Token Fetching
    openaire_client_id: str | None = Field(
        default=None,
        description="OpenAIRE Client ID for OAuth2 (required for client_credentials)",
    )
    openaire_client_secret: str | None = Field(
        default=None,
        description="OpenAIRE Client Secret for OAuth2 (required for client_credentials)",
    )
    # Token URL is fetched from constants, but could be overridden via env if needed
    openaire_token_url: str = Field(
        default=REGISTERED_SERVICE_API_TOKEN_URL,
        description="OAuth2 Token Endpoint URL",
    )


# Create a single, cached instance of settings
@lru_cache
def get_settings() -> ApiSettings:
    """
    Provides access to the application settings.

    Settings are loaded from environment variables (prefixed with 'AIRELOOM_')
    or .env/secrets.env files. The instance is cached for performance.

    Returns:
        ApiSettings: The application settings instance.
    """
    # Check if running in a test environment and potentially load test-specific env
    # For now, relies on standard .env/.secrets.env loading
    return ApiSettings()
