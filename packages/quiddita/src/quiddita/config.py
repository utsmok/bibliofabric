"""Settings for the Wikidata client.

Loaded from environment variables prefixed with ``QUIDDITA_`` and a
``.env`` file in the working directory.
"""

from functools import lru_cache

from bibliofabric.config import BaseApiSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict

#: The Wikidata etiquette guides (``Wikidata:Data_access`` and
#: ``Wikidata:Data_access/Large_volume``) ask readers to send requests in
#: series with a delay, roughly one request every 500 milliseconds. The
#: default follows that advice.
DEFAULT_MAX_REQUESTS_PER_SECOND = 2.0

#: Serial requests. The same guides ask readers not to run requests in
#: parallel against ``www.wikidata.org``.
DEFAULT_MAX_CONCURRENCY = 1

#: The SPARQL query service (``Wikidata:SPARQL_query_service``) asks readers
#: to run one query at a time and cancels queries that run longer than its
#: timeout. The ``sparql`` rate class paces queries at one every two seconds.
DEFAULT_SPARQL_REQUESTS_PER_SECOND = 0.5


def _default_rate_limits() -> dict[str, float | None]:
    return {"sparql": DEFAULT_SPARQL_REQUESTS_PER_SECOND}


class QuidditaSettings(BaseApiSettings):
    """Wikidata-specific client settings.

    Inherits ``timeout``, ``max_retries``, ``max_retry_wait``,
    ``max_requests_per_second``, ``max_concurrency``, ``user_agent`` and
    ``mailto`` from :class:`bibliofabric.config.BaseApiSettings`. The API
    needs no credentials, but the MediaWiki Action API, the Wikibase REST
    API, and the SPARQL query service all ask for a descriptive
    ``User-Agent`` with contact information: ``effective_user_agent()``
    builds it from ``user_agent`` or the package metadata, and ``mailto``
    is appended when it is set.
    """

    model_config = SettingsConfigDict(
        env_prefix="QUIDDITA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    max_requests_per_second: float | None = Field(
        default=DEFAULT_MAX_REQUESTS_PER_SECOND, gt=0
    )
    max_concurrency: int = Field(default=DEFAULT_MAX_CONCURRENCY, gt=0)
    rate_limits: dict[str, float | None] = Field(default_factory=_default_rate_limits)


@lru_cache
def get_settings() -> QuidditaSettings:
    """Return the process-wide settings, loaded once from the environment."""
    return QuidditaSettings()
