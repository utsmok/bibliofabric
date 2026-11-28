"""Settings for the Zenodo client.

Loaded from environment variables prefixed with ``ZENOTHECA_`` and a
``.env`` file in the working directory.
"""

from functools import lru_cache
from typing import Self

from bibliofabric.config import BaseApiSettings
from pydantic import Field, model_validator
from pydantic_settings import SettingsConfigDict

from .dialect import ZENODO_SEARCH_RATE_CLASS, ZENODO_SEARCH_REQUESTS_PER_SECOND

#: Every route except the two search routes allows 133 requests per minute
#: without a token (about 2.2 per second). The default stays below it.
DEFAULT_MAX_REQUESTS_PER_SECOND = 2.0
DEFAULT_MAX_CONCURRENCY = 5


def _default_rate_limits() -> dict[str, float | None]:
    """Return the per-class request limits: the ``search`` class of the search routes."""
    return {ZENODO_SEARCH_RATE_CLASS: ZENODO_SEARCH_REQUESTS_PER_SECOND}


class ZenothecaSettings(BaseApiSettings):
    """Zenodo-specific client settings.

    Inherits ``timeout``, ``max_retries``, ``max_retry_wait``,
    ``max_requests_per_second``, ``max_concurrency``, ``rate_limits``,
    ``user_agent`` and ``mailto`` from :class:`bibliofabric.config.BaseApiSettings`
    and sets Zenodo defaults: 2 requests per second, concurrency 5, and a
    ``search`` class at one request every 2 seconds for the two search
    routes, which allow 30 requests per minute without a token. Public
    reads need no credentials. Zenodo rejects requests without a
    ``User-Agent`` header; the client always sends one.
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
    rate_limits: dict[str, float | None] = Field(default_factory=_default_rate_limits)
    api_token: str | None = Field(default=None, repr=False)
    """Optional Zenodo access token.

    Sent as ``Authorization: Bearer``; lifts the page size cap from 25 to
    the documented 100 and grants access to private record reads. Public
    reads work without it.
    """

    @model_validator(mode="after")
    def _sync_rate_limits_with_explicit_pace(self) -> Self:
        """Drop the per-class limits when the caller sets the overall pace alone.

        ``ZenothecaSettings(max_requests_per_second=None)`` then disables pacing
        for every request class, including ``search``, unless ``rate_limits``
        is passed as well.
        """
        if (
            "max_requests_per_second" in self.model_fields_set
            and "rate_limits" not in self.model_fields_set
        ):
            self.rate_limits = {}
        return self


@lru_cache
def get_settings() -> ZenothecaSettings:
    """Return the process-wide settings, loaded once from the environment."""
    return ZenothecaSettings()
