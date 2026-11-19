# Authentication

Auth strategies implement the `AuthStrategy` protocol: `async_authenticate()`
mutates the outgoing `httpx.Request`, `async_close()` releases resources.

| Strategy | Use case |
|---|---|
| `NoAuth` | Public APIs (default) |
| `StaticTokenAuth(token)` | Pre-issued bearer token |
| `QueryParameterAuth(key_name, key_value)` | APIs authenticated by query parameter (OpenAlex `api_key`) |
| `HeaderAuth(name, value)` | Static credential headers (Crossref Plus `Crossref-Plus-API-Token`) |
| `ClientCredentialsAuth(client_id, client_secret, token_url)` | OAuth2 client-credentials flow |

`ClientCredentialsAuth` fetches a bearer token, reuses it until shortly before
`expires_in`, refreshes it on expiry, and serializes concurrent fetches. Pass
`user_agent=` so the token client identifies itself like the main client.
Missing credentials raise `ConfigurationError`; a failed token fetch raises
`AuthError`.

```python
from bibliofabric import ClientCredentialsAuth

auth = ClientCredentialsAuth(client_id, client_secret, token_url, user_agent=ua)
client = FooClient(auth=auth)
```

## API reference

::: bibliofabric.auth
    options:
      show_root_heading: true
