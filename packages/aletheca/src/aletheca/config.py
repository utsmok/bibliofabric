"""Aletheca settings for the OpenAlex API client.

Loaded from environment variables prefixed with ``ALETHECA_`` and a ``.env``
file in the working directory.
"""

from functools import lru_cache
from typing import Literal, Self

from bibliofabric.config import BaseApiSettings
from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import SettingsConfigDict

#: OpenAlex per-client request budget: 10-50 req/s by plan with lower caps for
#: boolean-heavy searches and semantic search; the safe general pace is 10.
DEFAULT_MAX_REQUESTS_PER_SECOND = 10.0
DEFAULT_MAX_CONCURRENCY = 5
#: OpenAlex caps ``search.semantic`` at 1 request/second on all plans.
DEFAULT_SEMANTIC_REQUESTS_PER_SECOND = 1.0

AuthScheme = Literal["query", "bearer"]
"""How the API key is sent: ``query`` (``?api_key=...``, the default) or
``bearer`` (``Authorization: Bearer ...``, required for collections writes)."""


def _default_rate_limits() -> dict[str, float | None]:
    """Return OpenAlex's default per-class request limits."""
    return {"semantic": DEFAULT_SEMANTIC_REQUESTS_PER_SECOND}


class AlethecaSettings(BaseApiSettings):
    """OpenAlex-specific client settings.

    Inherits ``timeout``, ``max_retries``, ``max_retry_wait``,
    ``max_requests_per_second``, ``max_concurrency``, ``rate_limits``,
    ``user_agent`` and ``mailto`` from :class:`bibliofabric.config.BaseApiSettings`
    and sets OpenAlex defaults (10 req/s, concurrency 5, semantic search 1 req/s).

    The polite pool no longer exists: since February 2026 OpenAlex ignores
    ``mailto`` and meters unkeyed traffic at $0.10/day per IP. A free API key
    raises the budget to $1/day and is required for cursor paging beyond the
    first page. Get one at https://openalex.org/settings/api.

    ``openalex_api_key`` (and env ``ALETHECA_OPENALEX_API_KEY``) is accepted at
    runtime as a deprecated alias for ``api_key``; typed callers should pass
    ``api_key=`` directly.
    """

    model_config = SettingsConfigDict(
        env_prefix="ALETHECA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: str | None = Field(
        default=None,
        repr=False,
        validation_alias=AliasChoices("api_key", "openalex_api_key"),
        description="OpenAlex API key; env names ALETHECA_API_KEY and the "
        "consumer-legacy ALETHECA_OPENALEX_API_KEY both work (the "
        "openalex_api_key constructor alias is runtime-only).",
    )
    auth_scheme: AuthScheme = Field(
        default="query",
        description="Send the key as the ``api_key`` query parameter or as an "
        "``Authorization: Bearer`` header.",
    )
    max_requests_per_second: float | None = Field(
        default=DEFAULT_MAX_REQUESTS_PER_SECOND, gt=0
    )
    max_concurrency: int = Field(default=DEFAULT_MAX_CONCURRENCY, gt=0)
    rate_limits: dict[str, float | None] = Field(default_factory=_default_rate_limits)

    @model_validator(mode="after")
    def _sync_rate_limits_with_explicit_pace(self) -> Self:
        """Clear default per-class caps when caller overrides overall pace alone.

        Ensures ``AlethecaSettings(max_requests_per_second=None)`` truly
        disables pacing for every request class (including ``semantic``) unless
        ``rate_limits`` is also passed explicitly.
        """
        if (
            "max_requests_per_second" in self.model_fields_set
            and "rate_limits" not in self.model_fields_set
        ):
            self.rate_limits = {}
        return self


@lru_cache
def get_settings() -> AlethecaSettings:
    """Return the process-wide settings, loaded once from the environment."""
    return AlethecaSettings()
