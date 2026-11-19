# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] - 2026-11-19

Overhaul of the public API. Versions of the client libraries after this
release: aireloom 0.8.0, aletheca 0.4.0, stavrophora 0.3.0; they pin
`bibliofabric>=0.6,<0.7`.

### Breaking changes

- Replaced the four resource mixins (`GettableMixin`, `SearchableMixin`,
  `CursorIterableMixin`, `PageIterableMixin`) and `BaseResourceClient` with one
  generic `ResourceClient[E]`, configured by a frozen `QueryDialect`.
  Behavior knobs are now hook methods (`build_filter_params`, `format_sort`,
  `build_batch_params`, `normalize_id`, `item_path`) instead of `_param_*`
  class attributes.
- `request()` always returns `httpx.Response` and raises on status >= 400:
  404 is `NotFoundError`, 429 is `RateLimitError`, 401/403 is `AuthError`,
  other statuses `APIError`. The silent raw-dict/`httpx.Response` fallbacks on
  validation failure are gone; `get()`, `search()`, and `iterate()` raise
  `ValidationError` carrying the rejected payload in `raw`.
- `search()` returns a generic `Page[E]` (results, total, next_cursor, page,
  meta) instead of an API-specific envelope or raw dict.
- `ResponseUnwrapper` methods were renamed to `results`, `item`, `total`,
  `next_cursor`, `meta` (was `unwrap_results`, `unwrap_single_item`,
  `get_next_page_token`, `get_total_results`).
- `BaseApiSettings` was reduced to the fields the client actually reads
  (`timeout`, `max_retries`, `max_retry_wait`, `max_requests_per_second`,
  `max_concurrency`, `user_agent`, `mailto`). Removed caching, pacing, hook,
  and rate-limit-buffer settings; subclasses set their own `env_prefix`.
- Removed: pre/post request hooks, response caching (`enable_caching`,
  `cache_*`, cachetools), rate-limit header pacing, `raw=` flags,
  `on_validation_error` hooks, `expected_model` parameters, `AuthStrategyType`,
  `get_base_settings()`, `DigMixin`/`safe_dig`, `ValidationErrorContext`,
  `BibliofabricRequestError`, `log_config.configure_logging()`, and the
  loguru dependency. The library uses standard `logging` and adds no handlers.
- `batch_get` moved into `ResourceClient` with signature
  `batch_get(ids, field="id", batch_size=None, concurrency=4)`; it returns a
  dict keyed by normalized id and omits missing ids.
- Retries are governed by an overridable `BaseApiClient.is_retryable(response)`
  (default: 429, 500, 502, 503, 504) and honor `Retry-After`, capped at
  `max_retry_wait`; the former lock-held buffer sleep and ignored Retry-After
  are gone.

### Added

- `HeaderAuth(name, value)` for static credential headers (Crossref Plus).
- `ClientCredentialsAuth` sends a `User-Agent` on its token client
  (`user_agent=` parameter).
- `APIError.body`: the parsed JSON error payload of error responses.
- `bibliofabric.ids`: `normalize_doi`, `is_doi`, `strip_url_prefix`,
  `normalize_orcid`, `normalize_ror`, `normalize_issn`.
- `bibliofabric.paging`: `QueryDialect` and `Page[E]`.
- `QueryDialect.iterate_page_size`: the page size `iterate()` uses when the
  caller passes none.
- `ResourceClient(client, path=...)`: per-instance paths for routes bound to a
  parent id, such as `members/{id}/works`.
- Cursor iteration stops when the API returns the request cursor unchanged
  (Solr-style exhaustion).
- `SafeList` now wraps a scalar string into `[value]` instead of a character
  list.
- Default `User-Agent` built from package metadata:
  `<package>/<version> (+<homepage>; mailto:<mailto>)`.
- Debug logs redact `api_key`, token query parameters, and auth headers.
- Tooling: `uv_build` backend, `py.typed` shipped, exact `ty` pin in the `dev`
  group, ruff linting `src` and `tests`, Keep a Changelog file, and a CI
  workflow with concurrency cancellation, least-privilege permissions, and
  tag-triggered trusted publishing.

## [0.5.2]

### Fixed

- Raise `NotFoundError` for model-backed requests that receive a 404 response.
- Redact query credentials such as `api_key` from request and exception logging.
- Add opt-in validation-failure hooks carrying the raw response body or rejected
  resource record and the validation exception.
- Add `raw=True` passthrough support to `BaseApiClient.request()` and resource
  `get()`/`search()` calls.
