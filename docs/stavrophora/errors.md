# Errors, retries, rate limits

## Exceptions

All errors subclass `bibliofabric.BibliofabricError` (re-exported from `stavrophora`):

| Exception | When |
|---|---|
| `NotFoundError` | 404 response |
| `RateLimitError` | 429 response after retries |
| `AuthError` | 401 or 403 response |
| `APIError` | any other error status; `.body` holds the parsed error payload |
| `NetworkError` | connection failed |
| `TimeoutError` | request exceeded `timeout` |
| `ValidationError` | a response record failed model validation; `.raw` holds the payload |
| `ConfigurationError` | a request the API would reject with 400, raised before sending |

Records that fail validation raise `ValidationError` during `iterate()`. Pass `on_error="skip"` with a `failures` list to drop them instead:

```python
failures = []
async for work in client.works.iterate(filters, on_error="skip", failures=failures):
    ...
```

## Retries

The client retries 429, 500, 502, 503, and 504 responses, plus network failures and timeouts. A `Retry-After` header is honored; other failures back off with jittered exponential waits capped at `max_retry_wait` (60 seconds by default). 403 and 404 are never retried. `max_retries` defaults to 3 and is configurable through `STAVROPHORA_MAX_RETRIES`.

A 403 from Crossref means the account was blocked, not throttled; stop and inspect the request rather than retrying.

## Rate limits

When `rate_limits`, `max_concurrency`, and `max_requests_per_second` are not explicitly set on `StavrophoraSettings`, `StavrophoraClient` picks pool-aware defaults based on your credentials:

| Pool | Credentials | `rate_limits` (req/s) | `max_concurrency` |
|---|---|---|---|
| Public | neither `mailto` nor `plus_token` | `{"single": 5.0, "list": 1.0}` | `1` |
| Polite | `mailto` set (no `plus_token`) | `{"single": 10.0, "list": 3.0}` | `3` |
| Metadata Plus | `plus_token` set | `{"single": 50.0, "list": 50.0}` | `10` |

Pacing follows the 2026-07 Crossref split per request class: top-level `/works` searches run in the `list` class, while single records, scoped `/.../works` routes, and all other routes run in the `single` class. The concurrency bound is shared across classes. Override each class through `STAVROPHORA_RATE_LIMITS` (a JSON object such as `{"single": 10.0, "list": 3.0}`) and the shared bound through `STAVROPHORA_MAX_CONCURRENCY`.

Every response is inspected by `StavrophoraClient.on_response()`, which captures Crossref's `x-api-pool`, `x-rate-limit-limit`, `x-rate-limit-interval`, and `x-concurrency-limit` headers into the read-only `client.last_pool` and `client.last_rate_limit_headers` properties.

On 429 the client backs off and retries automatically.
