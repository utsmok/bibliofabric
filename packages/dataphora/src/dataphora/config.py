"""Settings for the DataCite REST API client.

Loaded from environment variables prefixed with ``DATAPHORA_`` and a
``.env`` file in the working directory.
"""

from functools import lru_cache

from bibliofabric.config import BaseApiSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict

#: DataCite documents 500 anonymous requests per 5 minutes (1.67 req/s) and
#: sends no rate-limit headers. The default paces the client at 1.5 requests
#: per second, just under that budget.
DEFAULT_MAX_REQUESTS_PER_SECOND = 1.5
DEFAULT_MAX_CONCURRENCY = 3


class DataphoraSettings(BaseApiSettings):
    """DataCite-specific client settings.

    Inherits ``timeout``, ``max_retries``, ``max_retry_wait``,
    ``max_requests_per_second``, ``max_concurrency``, ``user_agent`` and
    ``mailto`` from :class:`bibliofabric.config.BaseApiSettings` and sets
    DataCite defaults (1.5 req/s, concurrency 3). Public reads need no
    credentials; the client never sends them.
    """

    model_config = SettingsConfigDict(
        env_prefix="DATAPHORA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    max_requests_per_second: float | None = Field(
        default=DEFAULT_MAX_REQUESTS_PER_SECOND, gt=0
    )
    max_concurrency: int = Field(default=DEFAULT_MAX_CONCURRENCY, gt=0)


@lru_cache
def get_settings() -> DataphoraSettings:
    """Return the process-wide settings, loaded once from the environment."""
    return DataphoraSettings()
