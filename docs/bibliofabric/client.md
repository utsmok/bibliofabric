# Client

`BaseApiClient` owns the HTTP lifecycle for every bibliofabric-family client: it
builds requests against a base URL, applies an auth strategy, throttles
concurrency and request rate, retries transient failures, and maps error
statuses to the bibliofabric exception hierarchy. It never parses response
models; resource clients do that through a `ResponseUnwrapper`.

## Behavior

- `request()` always returns an `httpx.Response` and raises on status >= 400:
  404 is `NotFoundError`, 429 is `RateLimitError`, 401/403 is `AuthError`,
  other statuses are `APIError`. Network failures raise `NetworkError` and
  timeouts raise `TimeoutError`.
- Retries cover 429, 500, 502, 503, 504, network failures, and timeouts, up to
  `settings.max_retries`. The wait honors the `Retry-After` header (seconds or
  HTTP date), capped at `settings.max_retry_wait`; otherwise it uses jittered
  exponential backoff.
- Override `is_retryable(response)` to veto retries, for example OpenAlex 429s
  with `reason: "daily_budget"` in the error body (exposed as `err.body`).
- Throttling is configured with `settings.max_requests_per_second` and
  `settings.max_concurrency`. The limiter never sleeps while holding a lock
  other requests need.
- Debug logs use standard `logging` with credential query parameters and auth
  headers redacted.
- A caller-owned `http_client` passed to the constructor is not closed by
  `aclose()`.

## API reference

::: bibliofabric.client
    options:
      show_root_heading: true
