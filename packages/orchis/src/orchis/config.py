"""Settings for the ORCID Public API client.

Loaded from environment variables prefixed with ``ORCHIS_`` and a ``.env``
file in the working directory.
"""

from functools import lru_cache

from bibliofabric.config import BaseApiSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict

#: ORCID allows 12 requests per second for anonymous and registered public
#: callers and 24 for member API callers, with a burst of 40 and daily read
#: quotas (25k reads per IP anonymously, 100k per client id for the public
#: API). The default keeps the client at a courtesy pace of 4 requests per
#: second, well inside the documented limits.
DEFAULT_MAX_REQUESTS_PER_SECOND = 4.0
DEFAULT_MAX_CONCURRENCY = 4


class OrchisSettings(BaseApiSettings):
    """ORCID-specific client settings.

    Inherits ``timeout``, ``max_retries``, ``max_retry_wait``,
    ``max_requests_per_second``, ``max_concurrency``, ``user_agent`` and
    ``mailto`` from :class:`bibliofabric.config.BaseApiSettings` and sets ORCID
    defaults (4 req/s, concurrency 4). The public API answers reads without
    credentials. A token lifts the daily read quota from 25,000 to 100,000
    reads per day for a registered public API client. Set ``access_token``
    to send a token you already hold, or set ``client_id`` and
    ``client_secret`` and the client mints a ``/read-public`` token itself
    on the first request. ``access_token`` wins when both are set.
    """

    model_config = SettingsConfigDict(
        env_prefix="ORCHIS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    max_requests_per_second: float | None = Field(
        default=DEFAULT_MAX_REQUESTS_PER_SECOND, gt=0
    )
    max_concurrency: int = Field(default=DEFAULT_MAX_CONCURRENCY, gt=0)
    access_token: str | None = None
    client_id: str | None = None
    client_secret: str | None = None


@lru_cache
def get_settings() -> OrchisSettings:
    """Return the process-wide settings, loaded once from the environment."""
    return OrchisSettings()
