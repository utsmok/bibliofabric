# Client

`BaseApiClient` owns the HTTP lifecycle for every bibliofabric-family client: it
builds requests against a base URL, applies an auth strategy, throttles
concurrency and request rate, retries transient failures, supports streaming
downloads, and maps error statuses to the bibliofabric exception hierarchy. It
never parses response models; resource clients do that through a
`ResponseUnwrapper`.

## Behavior

- `request()` always returns an `httpx.Response` and raises on status >= 400:
  404 is `NotFoundError`, 429 is `RateLimitError`, 401/403 is `AuthError`,
  other statuses are `APIError`. Network failures raise `NetworkError` and
  timeouts raise `TimeoutError`.
- `stream()` is an async context manager (sync context manager on
  `SyncBaseApiClient`) that yields an open `httpx.Response` for incremental
  reads with auth, rate limiting, `on_response()`, single-retry 401 token
  refresh, and typed error mapping.
- By default (`retry=None`), retries apply to idempotent HTTP methods (`GET`,
  `HEAD`, `OPTIONS`, `PUT`, `DELETE`) and cover 429, 500, 502, 503, 504,
  network failures, and timeouts, up to `settings.max_retries`. Pass
  `retry=True` to enable retries on `POST`/`PATCH` or `retry=False` to disable
  retries for a single call. The wait honors `Retry-After` (seconds or HTTP
  date), capped at `settings.max_retry_wait`; otherwise it uses jittered
  exponential backoff.
- Override `is_retryable(response)` to veto retries, for example OpenAlex 429s
  with `reason: "daily_budget"` in the error body (exposed as `err.body`).
- Override `on_response(response)` to observe every response (for example
  rate-limit headers or telemetry) before status errors are raised.
- Throttling is configured with `settings.max_requests_per_second`,
  `settings.rate_limits`, and `settings.max_concurrency`. Owned `httpx` clients
  also auto-size `httpx.Limits` from `max_concurrency` and honor
  `follow_redirects` and `connect_timeout`.
- Debug logs and exception strings redact built-in secret patterns plus any
  `redacted_query_params` / `redacted_headers` declared by the auth strategy.
- A caller-owned `http_client` passed to the constructor is not closed by
  `aclose()`.

## API reference

::: bibliofabric._async.client
    options:
      show_root_heading: true
