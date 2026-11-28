"""Settings for the OpenCitations client.

Loaded from environment variables prefixed with ``OPCITATO_`` and a
``.env`` file in the working directory.
"""

from functools import lru_cache

from bibliofabric.config import BaseApiSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict

#: Both APIs document a limit of 180 requests per minute per IP address
#: (3 requests per second). Higher unlimited rates need an OpenCitations
#: Access Token, which this client does not manage yet.
DEFAULT_MAX_REQUESTS_PER_SECOND = 3.0
DEFAULT_MAX_CONCURRENCY = 3


class OpcitatoSettings(BaseApiSettings):
    """OpenCitations client settings.

    Inherits ``timeout``, ``max_retries``, ``max_retry_wait``,
    ``max_requests_per_second``, ``max_concurrency``, ``user_agent`` and
    ``mailto`` from :class:`bibliofabric.config.BaseApiSettings` and sets the
    documented pace (3 req/s, concurrency 3). The APIs need no credentials;
    anonymous usage is limited to 180 requests per minute per IP.
    """

    model_config = SettingsConfigDict(
        env_prefix="OPCITATO_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    max_requests_per_second: float | None = Field(
        default=DEFAULT_MAX_REQUESTS_PER_SECOND, gt=0
    )
    max_concurrency: int = Field(default=DEFAULT_MAX_CONCURRENCY, gt=0)


@lru_cache
def get_settings() -> OpcitatoSettings:
    """Return the process-wide settings, loaded once from the environment."""
    return OpcitatoSettings()
