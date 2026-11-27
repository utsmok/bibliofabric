# Errors, retries, and limits

## Status mapping

`request()` and `stream()` raise on any status >= 400:

| Status | Exception |
|---|---|
| 404 | `NotFoundError` |
| 429 | `RateLimitError` (carries `retry_after` when sent) |
| 401, 403 | `AuthError` (carries `body` when JSON) |
| others | `APIError` |

Network failures raise `NetworkError`; timeouts raise `TimeoutError` (also a
builtin `TimeoutError`). Every exception exposes `.status_code`, `.request`,
and `.response` when available. `APIError` and `AuthError` expose `.body` with
the parsed JSON error payload and include a concise, sanitized summary of the
upstream body in `str(err)`, so callers see details like OpenAlex's
`reason=daily_budget` immediately. Custom credential query parameters declared
by an auth strategy (`redacted_query_params`) are scrubbed from both logs and
exception strings.

## Retries

By default (`retry=None`), automatic retries apply to idempotent HTTP methods
(`GET`, `HEAD`, `OPTIONS`, `PUT`, `DELETE`) and cover 429, 500, 502, 503, 504,
network failures, and timeouts, up to `settings.max_retries` (default 3,
meaning four attempts). Non-idempotent methods (`POST`, `PATCH`) are not
retried automatically unless the caller passes `retry=True` (for example on
read-only `POST` batch endpoints). Pass `retry=False` to disable retries for a
single call.

When the server sends `Retry-After` (seconds or HTTP date), the wait honors it
capped at `settings.max_retry_wait`; otherwise the client uses jittered
exponential backoff with the same cap.

For auth strategies that expose `invalidate_token()` (`ClientCredentialsAuth`,
`RefreshTokenAuth`), HTTP 401 triggers one automatic token invalidation and
retry before raising `AuthError`.

To veto retries, override `is_retryable(response)` on the client. A non-
retryable 429 surfaces immediately as `RateLimitError`:

```python
class FooClient(BaseApiClient):
    def is_retryable(self, response: httpx.Response) -> bool:
        if response.status_code == 429:
            try:
                body = response.json()
            except ValueError:
                body = None
            if isinstance(body, dict) and body.get("reason") == "daily_budget":
                return False
        return super().is_retryable(response)
```

Override `on_response(response)` to inspect every HTTP response (including
rate-limit headers or timings) before error statuses are raised.

## Limits

Three settings throttle the client: `max_requests_per_second` sets the
`"default"` rate class, `rate_limits` adds per-class rates (routed via
`rate_class(request)`), and `max_concurrency` bounds requests in flight
(default 10) and sizes the owned `httpx` connection pool. Set a class rate to
`None` to disable spacing for that class. The limiter reserves each caller's
pacing slot and sleeps before acquiring a concurrency slot, so waiting callers
of one class never starve another class.

## Configuration and validation failures

Passing unsupported search parameters (`query`, `select`, `sort`, `cursor`, or
`page`) for a resource's `QueryDialect`, or exceeding `QueryDialect.max_offset`,
raises `ConfigurationError` immediately before any HTTP request is sent.

Records that fail pydantic validation raise `ValidationError` carrying the
rejected payload in `raw` (use `bibliofabric.validate_model()` on custom
endpoints for the same wrapping). `search()`, `batch_get()`, `iterate()`, and
`collect()` can tolerate bad records with `on_error="skip", failures=my_list`;
each skipped record is appended to `failures` as a `(raw_record, exception)`
pair.
