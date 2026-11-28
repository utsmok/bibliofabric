"""Settings for the DOI System proxy client.

Loaded from environment variables prefixed with ``HODOI_`` and a ``.env``
file in the working directory.
"""

from functools import lru_cache

from bibliofabric.config import BaseApiSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict

#: doi.org publishes no rate limit and asks for polite use; the default
#: keeps the client at a courtesy pace of 2 requests per second.
DEFAULT_MAX_REQUESTS_PER_SECOND = 2.0
DEFAULT_MAX_CONCURRENCY = 2

#: Registration agencies answer metadata slowly at times; the default
#: timeout is generous on purpose.
DEFAULT_TIMEOUT = 60.0


class HodoiSettings(BaseApiSettings):
    """DOI System client settings.

    Inherits ``timeout``, ``max_retries``, ``max_retry_wait``,
    ``max_requests_per_second``, ``max_concurrency``, ``user_agent``,
    ``mailto`` and ``follow_redirects`` from
    :class:`bibliofabric.config.BaseApiSettings` and sets DOI defaults
    (2 req/s, concurrency 2, timeout 60 s). No credentials exist for doi.org.

    ``follow_redirects`` stays ``False``: the resolver answers metadata
    requests with a 302 whose body and ``Location`` header point at the
    registration agency's data server. Pass ``follow_redirects=True`` per
    request (the client does this for ``content()``), or set it to ``True``
    here to follow redirects globally.
    """

    model_config = SettingsConfigDict(
        env_prefix="HODOI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    timeout: float = Field(default=DEFAULT_TIMEOUT, gt=0)
    max_requests_per_second: float | None = Field(
        default=DEFAULT_MAX_REQUESTS_PER_SECOND, gt=0
    )
    max_concurrency: int = Field(default=DEFAULT_MAX_CONCURRENCY, gt=0)


@lru_cache
def get_settings() -> HodoiSettings:
    """Return the process-wide settings, loaded once from the environment."""
    return HodoiSettings()
