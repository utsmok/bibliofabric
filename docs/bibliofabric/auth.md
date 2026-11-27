# Authentication

Auth strategies implement the `AuthStrategy` protocol:
`async_authenticate()` / `authenticate()` mutate the outgoing `httpx.Request`,
and `async_close()` / `close()` release resources idempotently so a single
strategy instance works with both async and sync clients.

| Strategy | Use case |
|---|---|
| `NoAuth` | Public APIs (default) |
| `StaticTokenAuth(token)` | Pre-issued bearer token |
| `BasicAuth(username, password)` | HTTP Basic authentication (e.g. DataCite) |
| `QueryParameterAuth(key_name, key_value)` | APIs authenticated by query parameter (OpenAlex `api_key`) |
| `HeaderAuth(name, value)` | Static credential headers (Crossref Metadata Plus `crossref-api-key`) |
| `ClientCredentialsAuth(client_id, client_secret, token_url, ...)` | OAuth2 client-credentials flow (Basic or POST body credentials, optional `scope`) |
| `RefreshTokenAuth(token_url, refresh_token, ...)` | OAuth2 refresh-token flow with token caching and rotation |

## OAuth2 token caching and 401 refresh

`ClientCredentialsAuth` and `RefreshTokenAuth` fetch a bearer token, cache it
using `time.monotonic()` until shortly before `expires_in`, serialize
concurrent refreshes, and expose `invalidate_token()`. Pass `user_agent=`,
`scope=`, `timeout=`, or a caller-owned `http_client=` as needed. For token
endpoints that expect credentials in the form body rather than HTTP Basic
(such as ORCID), pass `token_auth_method="post"` to `ClientCredentialsAuth`.

When a request receives HTTP 401 and the auth strategy exposes
`invalidate_token()`, `BaseApiClient` invalidates the cached token and retries
the request once before raising `AuthError`.

Missing or invalid credentials raise `ConfigurationError`; a failed token fetch
raises `AuthError`.

```python
from bibliofabric import ClientCredentialsAuth, RefreshTokenAuth

auth = ClientCredentialsAuth(
    client_id,
    client_secret,
    token_url,
    scope="/read-public",
    token_auth_method="post",
    user_agent=ua,
)
client = FooClient(auth=auth)

refresh_auth = RefreshTokenAuth(
    token_url,
    refresh_token,
    client_id=client_id,
    client_secret=client_secret,
)
```

## Secret redaction

Auth strategies declare `redacted_query_params: frozenset[str]` and
`redacted_headers: frozenset[str]` (empty by default). Built-in strategies
populate these automatically (`QueryParameterAuth` redacts its `key_name`,
`HeaderAuth` redacts its header `name`, and bearer/basic/OAuth2 strategies
redact `authorization`), and `BaseApiClient` scrubs them from debug logs and
exception messages.

## API reference

::: bibliofabric.auth
    options:
      show_root_heading: true
