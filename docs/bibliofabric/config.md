# Configuration

`BaseApiSettings` is a [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
model holding the client's tunables. Subclass it per API, set an `env_prefix`
so the environment variables cannot collide across libraries, and add
API-specific fields.

```python
from pydantic_settings import SettingsConfigDict

from bibliofabric import BaseApiSettings


class FooSettings(BaseApiSettings):
    model_config = SettingsConfigDict(
        env_prefix="FOO_", env_file=".env", extra="ignore"
    )
```

Each client library exposes one `get_settings()` function decorated with
`functools.lru_cache` that returns its settings instance.

| Field | Default | Meaning |
|---|---|---|
| `timeout` | 30.0 | Request timeout in seconds (`> 0`) |
| `connect_timeout` | None | Optional TCP/TLS connect timeout in seconds (`> 0`); defaults to `timeout` |
| `follow_redirects` | False | Whether owned `httpx` clients follow HTTP 3xx redirects |
| `max_retries` | 3 | Retries per request (`>= 0`) |
| `max_retry_wait` | 60.0 | Upper bound on a single retry wait (`>= 0`) |
| `max_requests_per_second` | None | Default-class client-side rate limit (`> 0`); `None` disables it |
| `max_concurrency` | 10 | Shared concurrent requests bound (`> 0`); also auto-sizes connection pools |
| `rate_limits` | `{}` | Optional per-class rates (`dict[str, float \| None]`) used with `BaseApiClient.rate_class()` |
| `user_agent` | None | Overrides the default User-Agent |
| `mailto` | None | Contact address, added to the User-Agent |

When creating an owned `httpx.AsyncClient` / `httpx.Client`, `BaseApiClient`
auto-sizes `httpx.Limits` from `max_concurrency`:
`max_connections=max(20, max_concurrency * 2)` and
`max_keepalive_connections=max(10, max_concurrency)`.

When `user_agent` is not set, the client builds
`<package>/<version> (+<homepage>; mailto:<mailto>)` from the settings
subclass's package metadata.

## API reference

::: bibliofabric.config
    options:
      show_root_heading: true
