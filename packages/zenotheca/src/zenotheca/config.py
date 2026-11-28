"""Settings for the Zenodo client.

Loaded from environment variables prefixed with ``ZENOTHECA_`` and a
``.env`` file in the working directory.
"""

from functools import lru_cache

from bibliofabric.config import BaseApiSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict

#: Zenodo publishes no documented rate limit for unauthenticated callers.
#: The default keeps the client at a courtesy pace of 2 requests per second.
DEFAULT_MAX_REQUESTS_PER_SECOND = 2.0
DEFAULT_MAX_CONCURRENCY = 5


class ZenothecaSettings(BaseApiSettings):
    """Zenodo-specific client settings.

    Inherits ``timeout``, ``max_retries``, ``max_retry_wait``,
    ``max_requests_per_second``, ``max_concurrency``, ``user_agent`` and
    ``mailto`` from :class:`bibliofabric.config.BaseApiSettings` and sets
    Zenodo defaults (2 req/s, concurrency 5). Public reads need no
    credentials. Zenodo rejects requests without a ``User-Agent`` header;
    the client always sends one.
    """

    model_config = SettingsConfigDict(
        env_prefix="ZENOTHECA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    max_requests_per_second: float | None = Field(
        default=DEFAULT_MAX_REQUESTS_PER_SECOND, gt=0
    )
    max_concurrency: int = Field(default=DEFAULT_MAX_CONCURRENCY, gt=0)
    api_token: str | None = Field(default=None, repr=False)
    """Optional Zenodo access token.

    Sent as ``Authorization: Bearer``; lifts the page size cap from 25 to
    the documented 100 and grants access to private record reads. Public
    reads work without it.
    """


@lru_cache
def get_settings() -> ZenothecaSettings:
    """Return the process-wide settings, loaded once from the environment."""
    return ZenothecaSettings()
