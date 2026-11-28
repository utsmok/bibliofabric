"""Settings for the ROR API client.

Loaded from environment variables prefixed with ``RORIFER_`` and a ``.env``
file in the working directory.
"""

from functools import lru_cache

from bibliofabric.config import BaseApiSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict

#: ROR publishes no limit for unauthenticated callers. The default keeps the
#: client at a courtesy pace of 10 requests per second.
DEFAULT_MAX_REQUESTS_PER_SECOND = 10.0
DEFAULT_MAX_CONCURRENCY = 5


class RoriferSettings(BaseApiSettings):
    """ROR-specific client settings.

    Inherits ``timeout``, ``max_retries``, ``max_retry_wait``,
    ``max_requests_per_second``, ``max_concurrency``, ``user_agent`` and
    ``mailto`` from :class:`bibliofabric.config.BaseApiSettings` and sets ROR
    defaults (10 req/s, concurrency 5). The API needs no credentials.
    """

    model_config = SettingsConfigDict(
        env_prefix="RORIFER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    max_requests_per_second: float | None = Field(
        default=DEFAULT_MAX_REQUESTS_PER_SECOND, gt=0
    )
    max_concurrency: int = Field(default=DEFAULT_MAX_CONCURRENCY, gt=0)


@lru_cache
def get_settings() -> RoriferSettings:
    """Return the process-wide settings, loaded once from the environment."""
    return RoriferSettings()
