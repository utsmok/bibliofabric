"""Client settings shared by bibliofabric-family clients.

Subclass :class:`BaseApiSettings` per API and set ``model_config`` with your
own ``env_prefix`` (for example ``SettingsConfigDict(env_prefix="ALETHECA_",
env_file=".env", extra="ignore")``). Add API-specific fields on the subclass.
"""

import math
from importlib.metadata import PackageNotFoundError, distribution

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseApiSettings(BaseSettings):
    """Tunable client behavior, loaded from environment variables and ``.env``."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    timeout: float = Field(default=30.0, gt=0)
    connect_timeout: float | None = Field(default=None, gt=0)
    """Optional TCP/TLS connect timeout in seconds (``> 0``); defaults to ``timeout``."""
    follow_redirects: bool = False
    """Whether owned ``httpx`` clients follow HTTP 3xx redirects."""
    max_retries: int = Field(default=3, ge=0)
    max_retry_wait: float = Field(default=60.0, ge=0)
    max_requests_per_second: float | None = Field(default=None, gt=0)
    """Requests per second of the ``"default"`` rate class."""
    max_concurrency: int = Field(default=10, gt=0)
    rate_limits: dict[str, float | None] = Field(default_factory=dict)
    """Requests per second per rate class (D-19).

    The ``"default"`` class comes from :attr:`max_requests_per_second`; keys
    here add further classes (for example ``{"single": 10.0, "list": 3.0}``)
    that a client's overridden ``rate_class`` assigns per request. Setting a
    class to ``None`` disables pacing for that class. Each class gets its own
    minimum-interval gate; the concurrency bound is shared.
    """
    user_agent: str | None = None
    mailto: str | None = None

    @field_validator(
        "timeout", "connect_timeout", "max_retry_wait", "max_requests_per_second"
    )
    @classmethod
    def _validate_finite_float(cls, value: float | None) -> float | None:
        if value is not None and not math.isfinite(value):
            raise ValueError("must be a finite number")
        return value

    @field_validator("rate_limits")
    @classmethod
    def _validate_rate_limits(
        cls, value: dict[str, float | None]
    ) -> dict[str, float | None]:
        for rate_class, rate in value.items():
            if rate is not None and (not math.isfinite(rate) or rate <= 0):
                raise ValueError(
                    f"rate_limits[{rate_class!r}] must be positive and finite or None, "
                    f"got {rate!r}"
                )
        return value

    def effective_user_agent(self) -> str:
        """Return ``user_agent`` or the default built from package metadata.

        The default has the form ``<package>/<version> (+<homepage>;
        mailto:<mailto>)``. ``mailto`` is included only when set, and the
        parenthesized part is omitted when neither homepage nor mailto exists.
        """
        if self.user_agent is not None:
            return self.user_agent
        package = type(self).__module__.partition(".")[0]
        version = "0.0.0"
        homepage = ""
        try:
            dist = distribution(package)
            version = dist.version
            for entry in dist.metadata.get_all("Project-URL") or []:
                name, _, url = entry.partition(",")
                if name.strip().lower() == "homepage":
                    homepage = url.strip()
                    break
            if not homepage:
                homepage = dist.metadata.get("Home-page") or ""
        except PackageNotFoundError:
            pass
        if homepage or self.mailto:
            inner = "; ".join(
                part
                for part in (homepage, f"mailto:{self.mailto}" if self.mailto else "")
                if part
            )
            return f"{package}/{version} (+{inner})"
        return f"{package}/{version}"


__all__ = ["BaseApiSettings"]
