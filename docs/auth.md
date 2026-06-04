# Authentication

bibliofabric provides a pluggable authentication system based on the `AuthStrategy` protocol. Implementations modify outgoing `httpx.Request` objects in-place — typically by adding an `Authorization` header.

## Built-in Strategies

| Strategy | Use Case |
|---|---|
| `NoAuth` | Public APIs, local development |
| `StaticTokenAuth` | APIs that accept a pre-issued Bearer token |
| `ClientCredentialsAuth` | OAuth2 client credentials grant (automatic token refresh) |

All strategies implement `async_authenticate(request)` and `async_close()`, making them interchangeable at runtime.

## Quick Example

```python
from bibliofabric.auth import StaticTokenAuth

auth = StaticTokenAuth(token="my-api-token")
# Pass to BaseApiClient — auth is applied automatically before each request
```

## API Reference

::: bibliofabric.auth
    options:
      show_source: false
      show_root_heading: true
