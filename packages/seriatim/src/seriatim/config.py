"""Settings for the ISSN Portal client.

Loaded from environment variables prefixed with ``SERIATIM_`` and a ``.env``
file in the working directory. The Portal needs no credentials; every read
route used here is free.
"""

from functools import lru_cache

from bibliofabric.config import BaseApiSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict

#: The ISSN Centre publishes no rate limit for the Portal. The default keeps
#: the client at a courtesy pace of one request per second.
DEFAULT_MAX_REQUESTS_PER_SECOND = 1.0
DEFAULT_MAX_CONCURRENCY = 2


class SeriatimSettings(BaseApiSettings):
    """ISSN Portal client settings.

    Inherits ``timeout``, ``max_retries``, ``max_retry_wait``,
    ``max_requests_per_second``, ``max_concurrency``, ``user_agent`` and
    ``mailto`` from :class:`bibliofabric.config.BaseApiSettings` and sets
    Portal defaults (1 request per second, concurrency 2). There is no
    credential field; the SRU Search API and OAI-PMH need a paid subscription
    and are not wrapped.
    """

    model_config = SettingsConfigDict(
        env_prefix="SERIATIM_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    max_requests_per_second: float | None = Field(
        default=DEFAULT_MAX_REQUESTS_PER_SECOND, gt=0
    )
    max_concurrency: int = Field(default=DEFAULT_MAX_CONCURRENCY, gt=0)


@lru_cache
def get_settings() -> SeriatimSettings:
    """Return the process-wide settings, loaded once from the environment."""
    return SeriatimSettings()
