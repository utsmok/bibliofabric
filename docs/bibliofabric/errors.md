# Errors, retries, and limits

## Status mapping

`request()` raises on any status >= 400:

| Status | Exception |
|---|---|
| 404 | `NotFoundError` |
| 429 | `RateLimitError` |
| 401, 403 | `AuthError` |
| others | `APIError` |

Network failures raise `NetworkError`; timeouts raise `TimeoutError` (also a
builtin `TimeoutError`). `APIError` and its subclasses expose `.body` with the
parsed JSON error payload, so callers can inspect responses like OpenAlex's
`{"reason": "daily_budget"}`.

## Retries

Retries cover 429, 500, 502, 503, 504, network failures, and timeouts, up to
`settings.max_retries` (default 3, meaning four attempts). When the server
sends `Retry-After` (seconds or HTTP date), the wait honors it capped at
`settings.max_retry_wait`; otherwise the client uses jittered exponential
backoff with the same cap.

To veto retries, override `is_retryable(response)` on the client. A non-
retryable 429 surfaces immediately as `RateLimitError`:

```python
class FooClient(BaseApiClient):
    def is_retryable(self, response: httpx.Response) -> bool:
        if (
            response.status_code == 429
            and response.json().get("reason") == "daily_budget"
        ):
            return False
        return super().is_retryable(response)
```

## Limits

Two settings throttle the client: `max_requests_per_second` spaces requests
out, and `max_concurrency` bounds requests in flight (default 10). Both
default to reasonable values; set `max_requests_per_second=None` to disable
spacing. The limiter never sleeps while holding a lock that other requests
need.

## Validation failures

Records that fail pydantic validation raise `ValidationError` carrying the
rejected payload in `raw`. Harvest loops can tolerate bad records with
`iterate(..., on_error="skip", failures=my_list)`; each skipped record is
appended to `failures` as a `(raw_record, exception)` pair.
