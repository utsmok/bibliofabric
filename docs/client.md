# Client

`BaseApiClient` is the core of the framework — a generic async HTTP client built on `httpx`. It manages the full request/response lifecycle: retries with exponential backoff, optional TTL caching for GET requests, rate-limit detection and throttling, pluggable authentication, and pre/post request hooks.

Specific API clients (e.g., AIREloom's `AireloomClient`) subclass this and provide a `ResponseUnwrapper` and a `base_url`. The framework handles the rest.

## Key Features

- **Retries**: Configurable max attempts and backoff factor via `BaseApiSettings`. Retries on 429 and 5xx by default.
- **Caching**: Optional in-memory `TTLCache` for GET requests. Disabled by default.
- **Rate Limiting**: Parses standard rate-limit headers (`X-RateLimit-*`, `Retry-After`) and throttles automatically.
- **Hooks**: `pre_request_hooks` and `post_request_hooks` for logging, metrics, or custom logic.
- **Validation capture**: `validation_error_hooks` and the per-request
  `on_validation_error` hook receive a `ValidationErrorContext` containing the raw
  response body and validation exception when model parsing fails.
- **Raw passthrough**: pass `raw=True` to `request()` to skip model validation and
  receive the original `httpx.Response`.
- **Error Mapping**: Translates `httpx` exceptions into the bibliofabric exception hierarchy (`APIError`, `TimeoutError`, `NetworkError`, etc.).

## API Reference

::: bibliofabric.client
    options:
      show_source: false
      show_root_heading: true
