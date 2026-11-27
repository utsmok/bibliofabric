# Bibliofabric

A generic, extensible Python framework for building asynchronous and synchronous
API clients for scholarly and bibliometric data sources.

Built on `httpx` and `pydantic`, bibliofabric handles the boilerplate every API
client needs: retries, throttling, authentication, paging, batch retrieval,
error mapping, and typed resource clients. A client library only adds what is
specific to its API.

## Who is this for?

bibliofabric is a framework for developers building API client libraries. It is
not an end-user library. You would use it to build a library like
[AIREloom](https://github.com/utsmok/bibliofabric/tree/main/packages/aireloom)
(OpenAIRE), which researchers then use directly.

## Core concepts

| Component | Role |
|---|---|
| `BaseApiClient` / `SyncBaseApiClient` | Generic async/sync HTTP client: retries, throttling, auth, error mapping |
| `QueryDialect` | Declares an API's paging, sort, search, and select parameters |
| `ResourceClient[E]` / `SyncResourceClient[E]` | Typed client for one endpoint: get, exists, search, iterate, count, batch_get |
| `Page[E]` | Uniform search result envelope |
| `ResponseUnwrapper` | Protocol for parsing API-specific JSON envelopes |
| `AuthStrategy` | Pluggable auth: bearer, query parameter, header, OAuth2 |
| `BaseApiSettings` | pydantic-settings configuration with env var support |

Start with the [quick start in the README](https://github.com/utsmok/bibliofabric/tree/main/packages/bibliofabric#building-a-client),
then read:

- [Client](client.md) — HTTP lifecycle, retries, throttling
- [Sync usage](sync.md) — generated sync twins (`SyncBaseApiClient`, `SyncResourceClient`)
- [Resources](resources.md) — `ResourceClient` and its hooks
- [Paging](paging.md) — dialects and `Page`
- [Unwrapping](unwrap.md) — the response envelope protocol
- [Errors, retries, limits](errors.md)
- [Configuration](config.md), [Authentication](auth.md),
  [Identifiers](ids.md), [Types](types.md), [Exceptions](exceptions.md)
- [Writing a client with sync support](authoring-sync.md)
