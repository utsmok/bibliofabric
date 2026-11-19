"""Stavrophora settings for the Crossref API client."""

from functools import lru_cache

from bibliofabric.config import BaseApiSettings
from pydantic_settings import SettingsConfigDict


class StavrophoraSettings(BaseApiSettings):
    """Crossref-specific tunables.

    Loaded from environment variables prefixed with ``STAVROPHORA_`` (or a
    ``.env`` file): ``STAVROPHORA_MAILTO`` for the polite pool, and
    ``STAVROPHORA_PLUS_TOKEN`` for a Metadata Plus key. Generic behavior
    (timeout, retries, pacing) is inherited from
    :class:`bibliofabric.config.BaseApiSettings`.
    """

    model_config = SettingsConfigDict(
        env_prefix="STAVROPHORA_", env_file=".env", extra="ignore"
    )

    #: Defaults per D-15: the polite pool allows 3 list requests per second
    #: with 3 concurrent requests; single-record routes would allow 10/s but
    #: one limiter per client uses the strictest relevant rate.
    max_requests_per_second: float | None = 3.0
    max_concurrency: int = 3

    #: Contact email; sent as the ``mailto`` query parameter so requests land
    #: in the Crossref polite pool.
    mailto: str | None = None

    #: Metadata Plus key, sent as ``crossref-api-key: Bearer <token>``.
    plus_token: str | None = None


@lru_cache
def get_settings() -> StavrophoraSettings:
    """Provide cached access to application settings."""
    return StavrophoraSettings()
