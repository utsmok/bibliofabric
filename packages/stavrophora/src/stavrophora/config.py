"""Stavrophora settings for the Crossref API client."""

from functools import lru_cache
from typing import Self

from bibliofabric.config import BaseApiSettings
from pydantic import Field, model_validator
from pydantic_settings import SettingsConfigDict


def _default_rate_limits() -> dict[str, float | None]:
    return {"single": 10.0, "list": 3.0}


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

    #: Defaults per D-19 and the 2026-07 polite-pool split: top-level
    #: ``/works`` searches are the ``list`` class at 3 requests/s, everything
    #: else (single records, scoped ``/.../works`` routes, other routes) the
    #: ``single`` class at 10 requests/s; ``max_concurrency`` is shared.
    rate_limits: dict[str, float | None] = Field(default_factory=_default_rate_limits)
    max_requests_per_second: float | None = Field(default=3.0, gt=0)
    max_concurrency: int = Field(default=3, gt=0)

    #: Contact email; sent as the ``mailto`` query parameter so requests land
    #: in the Crossref polite pool.
    mailto: str | None = None

    #: Metadata Plus key, sent as ``crossref-api-key: Bearer <token>``.
    plus_token: str | None = None

    @model_validator(mode="after")
    def _apply_uniform_rate_limit(self) -> Self:
        """Honor an explicit ``max_requests_per_second`` when ``rate_limits`` is unset.

        Setting ``max_requests_per_second=None`` (or a single uniform rate)
        without also specifying ``rate_limits`` clears the per-class map so
        every request class falls back to ``"default"`` (unthrottled or that
        uniform rate).
        """
        if (
            "max_requests_per_second" in self.model_fields_set
            and "rate_limits" not in self.model_fields_set
        ):
            self.rate_limits = {}
        return self


@lru_cache
def get_settings() -> StavrophoraSettings:
    """Provide cached access to application settings."""
    return StavrophoraSettings()
