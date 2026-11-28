# Errors, retries, and rate limits

Every error inherits from `BibliofabricError` (re-exported from `aletheca`), and carries the failed `httpx.Request` and, when available, the `httpx.Response`.

```
BibliofabricError
├── APIError                     # any other 4xx/5xx; body holds the parsed JSON
│   ├── NotFoundError            # 404
│   └── RateLimitError           # 429
├── AuthError                    # 401 and 403
├── NetworkError                 # DNS, connection refused, reset
├── TimeoutError                 # also a builtin TimeoutError
├── ConfigurationError           # bad input caught client-side
└── ValidationError              # a record failed model validation
```

Catch specific types where you can react, and `BibliofabricError` as a last resort:

```python
from aletheca import NotFoundError, RateLimitError

try:
    work = await client.works.get("W0000000000")
except NotFoundError:
    ...
except RateLimitError as e:
    print(e.body)  # parsed JSON error payload, or None
```

Error strings redact credential query parameters, so printing them never leaks your key.

## Client-side guards

Some mistakes fail before any request is sent, with a `ConfigurationError`:

- More than 100 pipe-joined values in one filter.
- Basic paging past OpenAlex's 10,000-result ceiling (`page * per_page > 10,000`), combining `page` with `cursor`, `page < 1`, or `page_size <= 0`.
- A `corpus` value outside `core`/`expansion`/`all` on `works.search()`.
- A `sample()` size outside 1 to 10,000.
- An unknown `search_scoped()` scope, `autocomplete()` entity type, or `auth_scheme`.

A record that fails model validation raises `ValidationError` with the raw payload (`raw`), the pydantic error (`error`), and the model name (`model_name`). In `search()`, `batch_get()`, `iterate()`, and `collect()`, pass `on_error="skip"` to drop bad records and collect them in a `failures` list instead.

## Retries

The client retries 429, 500, 502, 503, and 504 responses plus network errors and timeouts. A `Retry-After` header is honored when present; otherwise it waits with jittered exponential backoff, capped at `ALETHECA_MAX_RETRY_WAIT` (default 60 seconds). The number of attempts is `ALETHECA_MAX_RETRIES` (default 3).

One OpenAlex-specific veto: a 429 whose body carries `reason: "daily_budget"` is not retried, because it cannot succeed before the UTC midnight reset and retrying would only burn budget.

## Rate limits and budgets

OpenAlex meters requests in dollars per day, not requests per day. There is no polite pool: `mailto` is ignored.

| Access | Daily budget | Cursor paging |
|---|---|---|
| No key | $0.10/day per IP | First page only |
| Free key | $1/day | Full cursor paging |

Request types cost differently: plain list requests are cheapest, free-text search costs more (about 10x), and semantic search has its own per-second cap of 1 request. Content downloads cost the most.

Check your remaining budget for free:

```python
status = await live_or_keyed_client.rate_limit()
print(status.rate_limit.daily_remaining_usd)
```

`rate_limit()` reads the key from settings and never stores the echoed key value. Every HTTP response also updates `client.last_rate_limit_headers` with any `x-ratelimit-*` headers returned by OpenAlex.

### Credit and cost headers

Every response tells you what the request cost and what is left of the daily budget. `client.last_rate_limit_headers` holds these headers from the most recent response, with lower-case names and string values. OpenAlex sent the following headers on 2026-11-28:

| Header | Meaning | Example |
|---|---|---|
| `x-ratelimit-credits-used` | Credits the request used. A single-record lookup by id uses 0, and a list request uses 1. | `1` |
| `x-ratelimit-cost-usd` | Cost of the request in US dollars. | `0.0001` |
| `x-ratelimit-limit` | Daily budget in credits. | `10000` |
| `x-ratelimit-remaining` | Credits left today. | `9999` |
| `x-ratelimit-limit-usd` | Daily budget in US dollars. | `1` |
| `x-ratelimit-remaining-usd` | Dollars left today. | `0.9999` |
| `x-ratelimit-prepaid-remaining-usd` | Prepaid balance in US dollars. | `0` |
| `x-ratelimit-onetime-remaining` | Remaining one-time credits. | `0` |
| `x-ratelimit-reset` | Seconds until the budget resets at UTC midnight. | `77578` |

OpenAlex also lists `X-RateLimit-Credits-Required` and `X-RateLimit-Cost-Required-USD` in `Access-Control-Expose-Headers`. They were absent from successful responses; the names suggest that they report the price of a request that the budget cannot cover.

Read the cost of each request after it returns:

```python
page = await client.works.search({"publication_year": 2024})
headers = client.last_rate_limit_headers
print(headers.get("x-ratelimit-cost-usd"), headers.get("x-ratelimit-remaining-usd"))
```

The headers describe the last response only. Under concurrent requests, read them right after the call you want to measure, or call `rate_limit()` for the authoritative daily totals.

## Client-side pacing

Aletheca spaces requests to a default of 10 per second with at most 5 concurrent requests, and caps `search.semantic` requests to 1 per second via its `"semantic"` rate class. Change these with `ALETHECA_MAX_REQUESTS_PER_SECOND`, `ALETHECA_MAX_CONCURRENCY`, and `ALETHECA_RATE_LIMITS`.

## Keyless 401s

The most common 401 is cursor paging without a key. Aletheca replaces the opaque upstream body with an `AuthError` that names the fix: get a free key and set `ALETHECA_API_KEY` (or pass `api_key=` to `AlethecaClient`). A keyed client keeps the upstream message.
