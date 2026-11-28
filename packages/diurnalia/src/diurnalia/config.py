"""Settings for the DOAJ API client.

Loaded from environment variables prefixed with ``DIURNALIA_`` and a ``.env``
file in the working directory.
"""

from functools import lru_cache

from bibliofabric.config import BaseApiSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict

#: DOAJ documents a rate limit of two requests per second on all API routes
#: with bursts of up to five queued requests
#: (https://doaj.org/api/docs, "Is there an upload limit for uploading
#: articles, or a rate limit?"). The default keeps the client at half of the
#: documented limit to share the quota with other tooling.
DEFAULT_MAX_REQUESTS_PER_SECOND = 1.0
DEFAULT_MAX_CONCURRENCY = 2


class DiurnaliaSettings(BaseApiSettings):
    """DOAJ-specific client settings.

    Inherits ``timeout``, ``max_retries``, ``max_retry_wait``,
    ``max_requests_per_second``, ``max_concurrency``, ``user_agent`` and
    ``mailto`` from :class:`bibliofabric.config.BaseApiSettings` and sets DOAJ
    defaults (1 request per second, concurrency 2). The search routes need no
    credentials; write routes that need an admin key are out of scope.
    """

    model_config = SettingsConfigDict(
        env_prefix="DIURNALIA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    max_requests_per_second: float | None = Field(
        default=DEFAULT_MAX_REQUESTS_PER_SECOND, gt=0
    )
    max_concurrency: int = Field(default=DEFAULT_MAX_CONCURRENCY, gt=0)


@lru_cache
def get_settings() -> DiurnaliaSettings:
    """Return the process-wide settings, loaded once from the environment."""
    return DiurnaliaSettings()
