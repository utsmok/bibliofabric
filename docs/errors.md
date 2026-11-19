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

The polite pool limits depend on the request type (split introduced 2026-07):

- 3 requests per second for top-level `/works` lists (`x-api-pool: polite-array`)
- 10 requests per second for single records and scoped works routes (`polite-single`)
- 3 concurrent requests
- Limits apply per `mailto` address

Stavrophora paces every request at 3 per second with 3 concurrent slots, which stays under the strictest ceiling. Configure both through `STAVROPHORA_MAX_REQUESTS_PER_SECOND` and `STAVROPHORA_MAX_CONCURRENCY`. A Metadata Plus key raises the limit to 150 requests per second through the `crossref-api-key` header.

On 429 the client backs off and retries automatically.
