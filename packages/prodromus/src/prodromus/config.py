"""Settings for the bioRxiv and medRxiv API client.

Loaded from environment variables prefixed with ``PRODROMUS_`` and a ``.env``
file in the working directory.
"""

from functools import lru_cache

from bibliofabric.config import BaseApiSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict

#: api.biorxiv.org publishes no rate limit. One request per second over one
#: connection keeps a long harvest polite.
DEFAULT_MAX_REQUESTS_PER_SECOND = 1.0
DEFAULT_MAX_CONCURRENCY = 1


class ProdromusSettings(BaseApiSettings):
    """bioRxiv-specific client settings.

    Inherits ``timeout``, ``max_retries``, ``max_retry_wait``,
    ``max_requests_per_second``, ``max_concurrency``, ``user_agent`` and
    ``mailto`` from :class:`bibliofabric.config.BaseApiSettings`. The API
    needs no credentials.
    """

    model_config = SettingsConfigDict(
        env_prefix="PRODROMUS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    max_requests_per_second: float | None = Field(
        default=DEFAULT_MAX_REQUESTS_PER_SECOND, gt=0
    )
    max_concurrency: int = Field(default=DEFAULT_MAX_CONCURRENCY, gt=0)


@lru_cache
def get_settings() -> ProdromusSettings:
    """Return the process-wide settings, loaded once from the environment."""
    return ProdromusSettings()


__all__ = ["ProdromusSettings", "get_settings"]
