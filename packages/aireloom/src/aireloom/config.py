"""Settings for the AIREloom client, loaded from the environment or ``.env``."""

from functools import lru_cache

from bibliofabric.config import BaseApiSettings
from pydantic_settings import SettingsConfigDict

DEFAULT_GRAPH_BASE_URL = "https://api.openaire.eu/graph"
DEFAULT_SCHOLIX_BASE_URL = "https://api.scholexplorer.openaire.eu"
"""OpenAIRE identity-platform (Keycloak) endpoint; the legacy
``https://aai.openaire.eu/oidc/token`` endpoint was retired on 2026-11-02 and
returns 410 Gone."""
DEFAULT_TOKEN_URL = (
    "https://aai.openaire.eu/auth/realms/openaire/protocol/openid-connect/token"
)


class AireloomSettings(BaseApiSettings):
    """Tunable client behavior for the OpenAIRE Graph and Scholexplorer APIs.

    Every field can be set through an environment variable prefixed with
    ``AIRELOOM_`` (for example ``AIRELOOM_OPENAIRE_CLIENT_ID``) or a ``.env``
    file in the working directory.
    """

    model_config = SettingsConfigDict(
        env_prefix="AIRELOOM_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    base_url: str = DEFAULT_GRAPH_BASE_URL
    scholix_base_url: str = DEFAULT_SCHOLIX_BASE_URL

    # OAuth2 client credentials (registered service). Both must be set for
    # authenticated access; without them the client stays anonymous.
    openaire_client_id: str | None = None
    openaire_client_secret: str | None = None
    token_url: str = DEFAULT_TOKEN_URL

    # D-15: OpenAIRE allows about 7200 requests per rolling hour.
    max_requests_per_second: float | None = 2.0
    max_concurrency: int = 4

    # The Scholexplorer host sends no rate-limit headers, so self-throttle.
    scholix_max_requests_per_second: float | None = 1.0


@lru_cache
def get_settings() -> AireloomSettings:
    """Return the process-wide settings instance, loaded from the environment."""
    return AireloomSettings()
