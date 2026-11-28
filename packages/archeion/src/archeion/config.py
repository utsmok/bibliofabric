"""Settings for the arXiv API client.

Loaded from environment variables prefixed with ``ARCHEION_`` and a ``.env``
file in the working directory.
"""

from functools import lru_cache

from bibliofabric.config import BaseApiSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict

#: arXiv asks API callers to make no more than one request every three
#: seconds and to use a single connection
#: (https://info.arxiv.org/help/api/tou.html).
DEFAULT_MAX_REQUESTS_PER_SECOND = 1 / 3
DEFAULT_MAX_CONCURRENCY = 1


class ArcheionSettings(BaseApiSettings):
    """arXiv-specific client settings.

    Inherits ``timeout``, ``max_retries``, ``max_retry_wait``,
    ``max_requests_per_second``, ``max_concurrency``, ``user_agent`` and
    ``mailto`` from :class:`bibliofabric.config.BaseApiSettings` and sets the
    arXiv terms of use as defaults: one request every three seconds over one
    connection. The API needs no credentials.
    """

    model_config = SettingsConfigDict(
        env_prefix="ARCHEION_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    max_requests_per_second: float | None = Field(
        default=DEFAULT_MAX_REQUESTS_PER_SECOND, gt=0
    )
    max_concurrency: int = Field(default=DEFAULT_MAX_CONCURRENCY, gt=0)


@lru_cache
def get_settings() -> ArcheionSettings:
    """Return the process-wide settings, loaded once from the environment."""
    return ArcheionSettings()


__all__ = ["ArcheionSettings", "get_settings"]
