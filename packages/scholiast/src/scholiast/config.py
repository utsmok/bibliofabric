"""Settings for the Semantic Scholar client.

Loaded from environment variables prefixed with ``SCHOLIAST_`` and
a ``.env`` file in the working directory.
"""

from functools import lru_cache

from bibliofabric.config import BaseApiSettings
from pydantic import Field, SecretStr
from pydantic_settings import SettingsConfigDict

#: With an API key, Semantic Scholar guarantees 1 request per second on the
#: introductory tier. Without a key, callers share one pool whose headline
#: capacity is 1000 requests per second, but the pool is contended and the
#: API answers 429 often. The default paces the client at 1 request per
#: second, which works with and without a key.
DEFAULT_MAX_REQUESTS_PER_SECOND = 1.0
DEFAULT_MAX_CONCURRENCY = 1


class ScholiastSettings(BaseApiSettings):
    """Semantic Scholar client settings.

    Inherits ``timeout``, ``max_retries``, ``max_retry_wait``,
    ``max_requests_per_second``, ``max_concurrency``, ``user_agent`` and
    ``mailto`` from :class:`bibliofabric.config.BaseApiSettings`. The
    defaults pace the client at 1 request per second with concurrency 1,
    matching the guaranteed per-key limit of the API.

    ``api_key`` is optional. When set, it travels in the ``x-api-key``
    header and the caller gets its own rate allocation; without it the
    client runs on the shared anonymous pool, where any request may answer
    HTTP 429.
    """

    model_config = SettingsConfigDict(
        env_prefix="SCHOLIAST_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: SecretStr | None = None
    max_requests_per_second: float | None = Field(
        default=DEFAULT_MAX_REQUESTS_PER_SECOND, gt=0
    )
    max_concurrency: int = Field(default=DEFAULT_MAX_CONCURRENCY, gt=0)


@lru_cache
def get_settings() -> ScholiastSettings:
    """Return the process-wide settings, loaded once from the environment."""
    return ScholiastSettings()
