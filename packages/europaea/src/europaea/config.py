"""Settings for the Europe PMC client.

Loaded from environment variables prefixed with ``EUROPAEA_`` and a
``.env`` file in the working directory.
"""

from functools import lru_cache

from bibliofabric.config import BaseApiSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict

#: The Europe PMC documentation publishes no rate limit and no hard request
#: limit for the REST API. A search can take several seconds (the framework
#: timeout default of 30 seconds covers that). The default paces the client
#: at a courtesy 3 requests per second.
DEFAULT_MAX_REQUESTS_PER_SECOND = 3.0
DEFAULT_MAX_CONCURRENCY = 2


class EuropaeaSettings(BaseApiSettings):
    """Europe PMC-specific client settings.

    Inherits ``timeout``, ``max_retries``, ``max_retry_wait``,
    ``max_requests_per_second``, ``max_concurrency``, ``user_agent`` and
    ``mailto`` from :class:`bibliofabric.config.BaseApiSettings` and sets
    Europe PMC defaults (3 req/s, concurrency 2). The API needs no
    credentials.
    """

    model_config = SettingsConfigDict(
        env_prefix="EUROPAEA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    max_requests_per_second: float | None = Field(
        default=DEFAULT_MAX_REQUESTS_PER_SECOND, gt=0
    )
    max_concurrency: int = Field(default=DEFAULT_MAX_CONCURRENCY, gt=0)


@lru_cache
def get_settings() -> EuropaeaSettings:
    """Return the process-wide settings, loaded once from the environment."""
    return EuropaeaSettings()
