# Errors, retries, and rate limits

## Exceptions

AIREloom re-exports the bibliofabric exceptions; every error derives from
`BibliofabricError`:

| Exception | Raised when |
|---|---|
| `NotFoundError` | the API answers 404 |
| `AuthError` | token fetch or authentication fails |
| `RateLimitError` | the API answers 429 after retries |
| `TimeoutError` | the request exceeds the timeout |
| `NetworkError` | connection or DNS failure |
| `ValidationError` | a response record fails model validation |
| `ConfigurationError` | invalid client usage, such as an unknown sort field |

`ValidationError` carries the raw record. Pass `on_error="skip"` and a
`failures` list to `search` or `collect` to keep going past bad records and
inspect them afterwards.

## Retries

The core retries transient failures (429 and 5xx responses, network errors)
with exponential backoff and honors the `Retry-After` header. Only idempotent
GET requests retry; the client sends no mutating requests.

## Rate limits

According to the [OpenAIRE API terms](https://graph.openaire.eu/docs/apis/terms),
authenticated requests allow up to 7,200 requests per rolling hour (2 req/s),
while unauthenticated requests are documented at 60 requests per hour (though
live V4 responses currently report `x-ratelimit-limit: 7199`).

Client defaults follow the 7,200 req/hour allowance:

- Graph host: at most 2 requests per second, 4 concurrent requests
- Scholexplorer host: at most 1 request per second (no rate-limit headers,
  so the client self-throttles)

Change them through settings:

```python
settings = AireloomSettings(max_requests_per_second=1.0, max_concurrency=2)
client = AireloomClient(settings=settings)
```

## Authentication

Set `AIRELOOM_OPENAIRE_CLIENT_ID` and `AIRELOOM_OPENAIRE_CLIENT_SECRET` for
OAuth2 client-credentials access, or `AIRELOOM_OPENAIRE_REFRESH_TOKEN` (or
`refresh_token=`) for refresh-token access. Setting only one of client ID or
client secret raises `ConfigurationError`. The client posts to the Keycloak
token endpoint, caches the bearer token until shortly before it expires, and
serializes concurrent fetches. Without credentials, or with an explicit
`auth_strategy=` (`auth=` is a deprecated alias), the client behaves accordingly;
an explicit strategy always wins.

The legacy `https://aai.openaire.eu/oidc/token` endpoint was retired on
2026-11-02 and returns 410 Gone; the default token URL already points at the
Keycloak realm endpoint.

## Polite pool

Set `mailto` in the settings to attach your contact address to every V4
request for polite-pool admission. V3 routes reject `mailto`, so the client
attaches it to V4 requests only.
