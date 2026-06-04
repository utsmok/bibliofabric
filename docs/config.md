# Configuration

`BaseApiSettings` is a [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) model that provides all tunable parameters for `BaseApiClient`. It reads from environment variables and `.env` / `secrets.env` files.

API-specific clients inherit this class and set their own `env_prefix` (e.g., `AIRELOOM_` for AIREloom).

## Quick Example

```python
from bibliofabric.config import BaseApiSettings

# All defaults — reads from env vars with no prefix
settings = BaseApiSettings()

# Override specific values
settings = BaseApiSettings(request_timeout=60.0, max_retries=5)
```

## API Reference

::: bibliofabric.config
    options:
      show_source: false
      show_root_heading: true
