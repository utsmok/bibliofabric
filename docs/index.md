# Bibliofabric

A generic, extensible Python framework for building modern, asynchronous API clients for scholarly and bibliometric data sources.

Built on `httpx` and `asyncio`, bibliofabric handles the boilerplate every API client needs — retries, caching, rate limiting, authentication, pagination, and error handling — so you can focus on the parts specific to your API.

## Who Is This For?

bibliofabric is a **framework for developers building API client libraries**. It is not an end-user library. You would use bibliofabric to create a library like [AIREloom](https://github.com/utsmok/aireloom) (an OpenAIRE Graph client), which researchers and data scientists then use directly.

## Core Concepts

| Component | Role |
|---|---|
| **`BaseApiClient`** | Generic async HTTP client — retries, caching, rate limiting, hooks |
| **`AuthStrategy`** | Pluggable auth: NoAuth, static token, OAuth2 client credentials |
| **`ResponseUnwrapper`** | Protocol for parsing API-specific JSON response envelopes |
| **`Resource Mixins`** | Composable `GettableMixin`, `SearchableMixin`, `CursorIterableMixin`, `PageIterableMixin` |
| **`BaseApiSettings`** | pydantic-settings configuration with env var support |

## Quick Start

```python
from bibliofabric.client import BaseApiClient
from bibliofabric.config import BaseApiSettings
from bibliofabric.models import ResponseUnwrapper
from bibliofabric.resources import GettableMixin, BaseResourceClient

# 1. Implement ResponseUnwrapper for your API
class MyUnwrapper(ResponseUnwrapper):
    def unwrap_results(self, response_json: dict) -> list[dict]:
        return response_json.get("data", [])
    # ... implement remaining protocol methods

# 2. Compose resource clients with mixins
class ItemsClient(GettableMixin, BaseResourceClient):
    _entity_path = "items"

# 3. Build your client
class MyApiClient(BaseApiClient):
    def __init__(self, **kwargs):
        super().__init__(
            base_url="https://api.example.com/v1",
            response_unwrapper=MyUnwrapper(),
            settings=BaseApiSettings(),
            **kwargs,
        )
        self.items = ItemsClient(api_client=self)
```

For a complete, production-quality example, see [AIREloom](https://github.com/utsmok/aireloom) — an OpenAIRE Graph client built on bibliofabric.

## Key Features

- **Asynchronous by design** — built on `httpx` for non-blocking I/O
- **Extensible** — protocols and mixins for any API shape
- **Robust** — retries with exponential backoff, rate limit management, comprehensive error hierarchy
- **Type-safe** — fully typed with Pydantic models and generic protocols

## API Reference

Browse the module documentation for detailed API signatures:

- [Client](client.md) — `BaseApiClient` and the HTTP lifecycle
- [Configuration](config.md) — `BaseApiSettings` and environment configuration
- [Resources](resources.md) — mixins and `BaseResourceClient`
- [Models](models.md) — `ResponseUnwrapper` protocol
- [Authentication](auth.md) — auth strategies
- [Exceptions](exceptions.md) — error hierarchy
