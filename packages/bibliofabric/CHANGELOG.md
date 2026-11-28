# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.8.0] - 2026-11-28

Companion client versions built on this release: aireloom 0.9.1, aletheca 0.5.1,
and stavrophora 0.5.0 (all pinning `bibliofabric>=0.8,<0.9`), and the eleven
Wave 1 libraries.

### Added

- `BaseApiClient.default_headers` property: headers sent with every
  `request()` and `stream()` call, overridden per call by `headers=`.
- `follow_redirects: bool | None = None` on `BaseApiClient.request()` and
  `BaseApiClient.stream()`, overriding `BaseApiSettings.follow_redirects` for
  one call (for example to read the `Location` header of a DOI resolver's 3xx
  response, or to follow content-negotiation redirects).
- `ResourceClient.default_params()` hook: query parameters sent with every
  list, `count()`, and batch request.
- `ResourceClient.search_path(query)` hook: the list route for search,
  `count()`, and batch requests, for APIs that carry the query in the path.
  `query=` is accepted when the dialect has no `query_param` as long as the
  search path uses the query.
- `JsonApiUnwrapper` in `bibliofabric.unwrap`: reads JSON:API envelopes
  (`data`, `meta.total`, and the cursor query parameter in `links.next`).
- Identifier normalizers `normalize_isbn` (ISBN-10 to ISBN-13),
  `normalize_isni`, `normalize_arxiv`, `normalize_pmid`, `normalize_pmcid`,
  `normalize_wikidata_qid`, `normalize_gnd`, and `normalize_viaf`.

### Changed

- `normalize_ror` also strips the `ror.org/` and `https://www.ror.org/`
  prefixes.

## [0.7.0] - 2026-11-27

Companion client versions built on this release: aireloom 0.9.0, aletheca 0.5.0,
and stavrophora 0.4.0 (all pinning `bibliofabric>=0.7,<0.8`).

### Added

- `on_error` (`"raise"` / `"skip"`) and `failures` collector on
  `ResourceClient.search()` and `ResourceClient.batch_get()` (#16).
- Concise, sanitized upstream HTTP error body summaries in `APIError` and
  `AuthError` `__str__`, plus `APIError.status_code` and
  `RateLimitError.retry_after` (#18).
- `validate_model()` helper exported from `bibliofabric` (wrapping
  `pydantic.ValidationError` into `bibliofabric.ValidationError` with the
  offending payload attached) and `parse_json()` guarding 2xx JSON decoding.
- `select=` and `params=` passthrough on `ResourceClient.get()` and
  `id: str | int` identifier widening on resource lookups (`get()`,
  `exists()`, `item_path()`).
- `QueryDialect.count_page_size` to control the page size used by `count()`.
- Idempotent-by-default retry policy (`GET`, `HEAD`, `OPTIONS`, `PUT`, `DELETE`)
  with per-call `retry: bool | None = None` override on `BaseApiClient.request()`
  (enabling retries on read-only `POST` batch calls with `retry=True` or
  disabling retries with `retry=False`).
- `BaseApiSettings.follow_redirects` (default `False`) and
  `BaseApiSettings.connect_timeout` (default `None`), plus automatic
  `httpx.Limits` sizing (`max_connections=max(20, max_concurrency * 2)`,
  `max_keepalive_connections=max(10, max_concurrency)`) for owned `httpx`
  clients.
- `BasicAuth(username, password)` and `RefreshTokenAuth(token_url, refresh_token, ...)`
  auth strategies (exported from `bibliofabric` and `bibliofabric.auth`).
- `ClientCredentialsAuth` now supports `scope`, `token_auth_method`
  (`"basic"` or `"post"`), `timeout`, caller-owned `http_client`, and
  `invalidate_token()`.
- Single-retry-on-401 token refresh in `BaseApiClient.request()` and `stream()`
  when the auth strategy exposes `invalidate_token()`.
- Automatic custom credential redaction via `redacted_query_params` and
  `redacted_headers` on auth strategies (`QueryParameterAuth`, `HeaderAuth`,
  `BasicAuth`, `StaticTokenAuth`, OAuth2 strategies), applied to debug logs and
  exception messages.
- `BaseApiClient.on_response(response)` hook called after every HTTP response
  before status errors raise.
- `BaseApiClient.stream(method, path, *, params=None, headers=None, timeout=None)`
  context manager (async and sync) for streaming responses with auth, rate
  limiting, `on_response`, 401 refresh, and error mapping.
- Overridable `ResourceClient._fetch_batch_chunk(field, chunk, *, select=None)`
  hook so `POST`-batch and path-batch clients inherit chunking, deduplication,
  concurrency, validation, `on_error`/`failures`, and keying from `batch_get()`.
- Flexible `QueryDialect`: `page_size_param` may be `None` (unpaged APIs),
  `max_offset` caps page/offset depth, and `ResourceClient(..., dialect=...)`
  allows per-instance dialect overrides.
- Fast-path bulk validation using a lazily cached `TypeAdapter(list[E])` per
  `ResourceClient` subclass on the `on_error="raise"` path, falling back to
  per-record validation on failure so `ValidationError.raw` still attaches the
  offending record.
- Python 3.14 trove classifier in `pyproject.toml`.

### Changed

- `ResourceClient._search_params()` (plus `get()`, `batch_get()`, and
  `iterate()`) now fail fast with `ConfigurationError` when callers pass
  `query`, `select`, `sort`, `cursor`, or `page` against a `QueryDialect` that
  does not declare the corresponding parameter.
- `BaseApiSettings` validates positive/non-negative bounds and finiteness for
  `timeout`, `max_retries`, `max_retry_wait`, `max_requests_per_second`,
  `max_concurrency`, and `rate_limits` entries (allowing `None` to disable
  pacing for a specific rate class).

### Fixed

- Non-starving O(1) `Limiter`: reserves rate-class slots monotonically before
  acquiring concurrency slots so long spacing or 429 backoff sleeps do not
  block sibling classes or workers.
- `ResourceClient.first()` now requests `page_size=1` instead of fetching a full
  default page.
- `ResourceClient.count()` omits the cursor parameter for page/offset and
  hybrid dialects (cursor-only dialects still send `cursor_start`) and honors
  `QueryDialect.count_page_size`.
- Injected `http_client` instances now resolve `base_url` properly and receive
  the configured `User-Agent` header when not already set.
- `ClientCredentialsAuth` uses monotonic clocks for token expiry, handles
  missing/short expiry cleanly, and surfaces token-endpoint errors consistently.
- `normalize_orcid()` strips trailing slashes and validates digit/checksum
  format before hyphenating; `normalize_ror()` strips trailing slashes before
  lowercasing.

## [0.6.0] - 2026-11-26

Overhaul of the public API. Versions of the client libraries after this
release: aireloom 0.8.0, aletheca 0.4.0, stavrophora 0.3.0; they pin
`bibliofabric>=0.6,<0.7`.

### Changed

- Auth strategies implement both method pairs
  (`async_authenticate`/`async_close` and `authenticate`/`close`), so one
  strategy object works with either client variant. `ClientCredentialsAuth`
  lazily creates an `httpx.AsyncClient` or `httpx.Client` per variant, guards
  each variant's refresh with its own lock, and shares the cached token.
- The `bibliofabric.client` and `bibliofabric.resources` module paths are
  gone; import `BaseApiClient`, `ResourceClient`, and `OnError` from the
  package root.
- `ResourceClient.batch_get` bounds its chunk fetches through the shared
  `run_bounded` primitive instead of a local semaphore + `gather`.
- Search text is keyword-only (`query=`), and a string passed in the
  `filters` position raises `ConfigurationError` naming `query=` before any
  request is sent. Before, a positional query was sent as the `page`
  parameter (#12).

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

- Sync twins generated from the async source (D-17): the I/O modules live in
  `bibliofabric._async`, and `scripts/unasync.py` generates the committed
  `bibliofabric._sync` package plus sync test modules. The package root now
  also exports `SyncBaseApiClient` and `SyncResourceClient`; sync twins work
  inside a running event loop because they never touch one.
- Request-class limiter (D-19): `BaseApiSettings.rate_limits` declares
  requests-per-second per class (`max_requests_per_second` remains the rate of
  the `"default"` class), and `BaseApiClient.rate_class(request)` is the
  overridable hook that assigns a class per request. Each class gets its own
  minimum-interval gate; the concurrency bound is shared.
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
