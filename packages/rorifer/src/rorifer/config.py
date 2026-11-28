"""Settings for the ROR API client.

Loaded from environment variables prefixed with ``RORIFER_`` and a ``.env``
file in the working directory.
"""

from functools import lru_cache
from typing import Self

from bibliofabric.config import BaseApiSettings
from pydantic import Field, model_validator
from pydantic_settings import SettingsConfigDict

from .dialect import ZENODO_SEARCH_REQUESTS_PER_SECOND

#: ROR documents a limit of 2,000 requests per 5 minutes per IP address,
#: about 6.7 requests per second. The default stays below it.
DEFAULT_MAX_REQUESTS_PER_SECOND = 6.0
DEFAULT_MAX_CONCURRENCY = 5


def _default_rate_limits() -> dict[str, float | None]:
    """Return the per-class request limits: the ``zenodo`` class of the dump helper."""
    return {"zenodo": ZENODO_SEARCH_REQUESTS_PER_SECOND}


class RoriferSettings(BaseApiSettings):
    """ROR-specific client settings.

    Inherits ``timeout``, ``max_retries``, ``max_retry_wait``,
    ``max_requests_per_second``, ``max_concurrency``, ``rate_limits``,
    ``user_agent`` and ``mailto`` from :class:`bibliofabric.config.BaseApiSettings`
    and sets ROR defaults: 6 requests per second, concurrency 5, and a
    ``zenodo`` class at one request every 2 seconds for the data dump
    helper, because the anonymous Zenodo search accepts 30 requests per
    minute. The API needs no credentials.
    """

    model_config = SettingsConfigDict(
        env_prefix="RORIFER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    max_requests_per_second: float | None = Field(
        default=DEFAULT_MAX_REQUESTS_PER_SECOND, gt=0
    )
    max_concurrency: int = Field(default=DEFAULT_MAX_CONCURRENCY, gt=0)
    rate_limits: dict[str, float | None] = Field(default_factory=_default_rate_limits)

    @model_validator(mode="after")
    def _sync_rate_limits_with_explicit_pace(self) -> Self:
        """Drop the per-class limits when the caller sets the overall pace alone.

        ``RoriferSettings(max_requests_per_second=None)`` then disables pacing
        for every request class, including ``zenodo``, unless ``rate_limits``
        is passed as well.
        """
        if (
            "max_requests_per_second" in self.model_fields_set
            and "rate_limits" not in self.model_fields_set
        ):
            self.rate_limits = {}
        return self


@lru_cache
def get_settings() -> RoriferSettings:
    """Return the process-wide settings, loaded once from the environment."""
    return RoriferSettings()
