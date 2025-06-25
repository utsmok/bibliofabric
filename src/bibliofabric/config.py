# bibliofabric/config.py
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .types import PostRequestHook, PreRequestHook


class BaseApiSettings(BaseSettings):
    """
    Manages user-configurable settings for API clients built on bibliofabric,
    primarily loaded from environment variables or a .env file.

    This base class provides generic configuration options for HTTP client behavior,
    caching, rate limiting, and request hooks that can be inherited by specific
    API client implementations.
    """

    model_config = SettingsConfigDict(
        env_file=(".env", "secrets.env"),  # Look in both .env and secrets.env
        env_file_encoding="utf-8",
        # Environment variables should be prefixed by the specific implementation
        env_prefix="",  # To be overridden by inheriting classes
        extra="ignore",  # Ignore extra fields found in environment
        case_sensitive=False,  # Allow flexible casing in environment variables
        arbitrary_types_allowed=True,  # Allow hook callables
    )

    # --- Client Behavior Settings ---
    request_timeout: float = Field(
        default=30.0, description="Default request timeout in seconds"
    )
    max_retries: int = Field(
        default=3, description="Maximum number of retries for failed requests"
    )
    backoff_factor: float = Field(
        default=0.5, description="Backoff factor for retries (seconds)"
    )
    user_agent: str = Field(
        default="bibliofabric/1.0.0",
        description="User-Agent header for requests",
    )

    # --- Rate Limiting Settings ---
    enable_rate_limiting: bool = Field(
        default=True, description="Enable/disable API rate limiting features"
    )
    rate_limit_buffer_percentage: float = Field(
        default=0.1,
        description="Buffer percentage to consider rate limit approaching (e.g., 0.1 for 10%)",
    )
    rate_limit_retry_after_default: int = Field(
        default=60,
        description="Default wait time in seconds if Retry-After header is not present on 429",
    )

    # --- Caching Settings ---
    enable_caching: bool = Field(
        default=False, description="Enable/disable client-side caching"
    )
    cache_ttl_seconds: int = Field(
        default=300,
        description="Default TTL for cache entries in seconds (e.g., 300 for 5 minutes)",
    )
    cache_max_size: int = Field(
        default=128, description="Maximum number of items in the LRU cache"
    )

    # --- Hook Settings ---
    pre_request_hooks: list[PreRequestHook] = Field(
        default_factory=list,
        description="List of hooks to call before a request is made.",
    )
    post_request_hooks: list[PostRequestHook] = Field(
        default_factory=list,
        description="List of hooks to call after a response is received and parsed.",
    )


# Create a single, cached instance of settings
@lru_cache
def get_base_settings() -> BaseApiSettings:
    """
    Provides access to the base API settings.

    Settings are loaded from environment variables or .env/secrets.env files.
    The instance is cached for performance.

    Note: This function provides only the base settings. Specific API client
    implementations should provide their own settings factory functions.

    Returns:
        BaseApiSettings: The base API settings instance.
    """
    return BaseApiSettings()
