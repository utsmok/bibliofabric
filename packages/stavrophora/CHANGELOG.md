# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Requires `bibliofabric>=0.8,<0.9` (the workspace core is now 0.8.0).

## [0.4.0] - 2026-11-27

### Added

- Pool-aware default rate limits in `StavrophoraClient` when `rate_limits`, `max_concurrency`, and `max_requests_per_second` are not explicitly configured: Metadata Plus (`plus_token` set) defaults to `{"single": 50.0, "list": 50.0}` with `max_concurrency=10`, Polite Pool (`mailto` set) to `{"single": 10.0, "list": 3.0}` with `max_concurrency=3`, and Public Pool (neither set) to `{"single": 5.0, "list": 1.0}` with `max_concurrency=1`.
- `StavrophoraClient.on_response()` captures Crossref pool and rate-limit headers (`x-api-pool`, `x-rate-limit-limit`, `x-rate-limit-interval`, `x-concurrency-limit`) into read-only `last_pool` and `last_rate_limit_headers` properties.
- `WorksResource.latest_version(..., update_types=("new_version", "new_edition"))`: filters `updated-by` entries by type by default so retractions and corrections are not mistaken for newer versions; pass `update_types=None` to follow all Crossmark updates.
- `on_error` / `failures` passthrough aligned with `bibliofabric` across resource `search()` and `batch_get()` calls.
- Added model fields `Work.published_other`, `Work.content_created`, `Work.content_updated`, `CrossRefDate.version`, and `Event.theme`, and widened `Funder.hierarchy` to `dict[str, Any] | None`.
- Exported `JournalsResource` and `LicensesResource` in `stavrophora.__all__`.
- Added `"Programming Language :: Python :: 3.14"` classifier in `pyproject.toml`.

### Changed

- Updated `bibliofabric` dependency to `>=0.7,<0.8`.
- `CrossrefResourceClient.item_path()` now percent-encodes identifiers with `quote(..., safe="")` (sending `%2F` inside DOIs per Crossref recommendation, matching `FundersResource.works()`).
- Extracted `_WorksListResource` holding shared list, search, iterate, count, facets, sample, and batch methods; `WorksResource(_WorksListResource)` adds `get`, `exists`, `agency`, and `latest_version`, while `ScopedWorksResource(_WorksListResource)` omits single-work methods statically under `ty` and at runtime.
- Aligned `CrossrefDialect` / `CrossrefOffsetDialect` (`max_offset=10_000`, `sort_param=None` and `select_param=None` on offset routes) and `TypesResource` (`CrossrefUnpagedDialect` with `page_size_param=None`) with `bibliofabric` fail-fast `_search_params()`.
- Widened `WorksFilters`, `MemberFilters`, and `FunderFilters` fields to accept sequences and integer IDs, and widened single-resource identifier typing (`str | int`, e.g. `members.get(297)`).
- `Work.event.sponsor` is a list of strings (`SafeStrList`, empty when absent) instead of `str | None`; a single sponsor parses as a one-item list (#15).

### Fixed

- Split cursor-enabled `CrossrefDialect` from offset-only `CrossrefOffsetDialect`, fixing invalid `cursor=*` queries on non-works endpoints and handling unpaged `/types` `count()` / `iterate()` cleanly.
- Propagated constructor `mailto=` into `StavrophoraSettings` so the `User-Agent` header includes the caller's address.
- Fixed the `rate_limits` settings validator so an explicit `max_requests_per_second` override controls pacing instead of being shadowed by default class rates.
- Fixed `rate_class()` URL path regex matching for top-level `/works` vs scoped and single-item routes.
- Wrapped `works.agency()` validation through `bibliofabric.validate_model` (raising `bibliofabric.ValidationError` instead of raw `pydantic.ValidationError`) and guarded JSON decoding with `parse_json`.
- Fixed `FunderWorksResource` (`funders.works(..., include_descendants=True)`) so `facets()` and `sample()` apply descendant funder filters as well.
- Fixed `rows=0` handling for `facets()` requests and hardened client-side route guards across endpoints.
- `Work.event.sponsor` accepts the list Crossref prints for conferences with several sponsors (ACM proceedings). One such record on a page raised `ValidationError` for the whole `search()` result, and `works.get()` failed for the record itself (#15).
- Resolved all `ty` diagnostics in `packages/stavrophora/tests/` so `ty check` passes with zero diagnostics and zero ignore comments across both `src/` and `tests/`.

## [0.3.0] - 2026-11-26

### Changed

- Pacing is per request class (D-19): top-level `/works` searches run at
  3 requests/s (`list` class), everything else — single records, scoped
  `/.../works` routes, and all other routes — at 10 requests/s (`single`
  class), with the 3 polite concurrency slots shared across classes. The
  client no longer paces every request at the strictest rate. Configure the
  classes with `rate_limits` / `STAVROPHORA_RATE_LIMITS` (JSON object).

### Added

- Sync twins: `StavrophoraSyncClient` and the `Sync*` resource classes, generated from the async source with `scripts/unasync.py`. Same parameters, errors, paging, and per-class pacing as the async client; the sync client never touches an event loop, so it works in scripts, notebooks, and inside a running event loop.
- `works.exists(doi)`: HEAD-based existence check that returns False on 404.
- `works.latest_version(doi)`: resolves a DOI to the newest record in its Crossmark update chain via `updated-by`.
- `funders.descendants(funder_id)` and `include_descendants=True` on `funders.works()`, which ORs the descendant funder ids into the `funder` filter.
- `journals.dois_by_year(issn)`: DOI counts per issued year from the journal record's breakdowns.

### Breaking

Rewritten onto the bibliofabric 0.6 core (`ResourceClient`, `QueryDialect`, `Page`). Summary of breaking changes:

- `StavrophoraSession` removed. Use `StavrophoraClient` directly (it is the async context manager).
- `search()` returns `bibliofabric.Page` (`.results`, `.total`, `.next_cursor`, `.meta`) instead of the `ApiResponse` envelope. The `ApiResponse` and `Message` models are removed.
- `search()` signature renamed: `search=` is now `query=`, `sort_by="field:desc"` is now `sort="field:desc"`, and `raw` / `on_validation_error` are gone (parse failures raise `bibliofabric.ValidationError` with the raw payload attached).
- `endpoints.py` renamed to `filters.py` (`from stavrophora import WorksFilters` works as before).
- `iterate()` signature aligned with the framework (`filters` first positional; `on_error="raise"|"skip"` instead of `"raw"`; `on_validation_error` gone). It defaults to 1000 rows and rejects the `issued` / `published*` sorts the API no longer allows with cursors.
- `constants.py`, `_helpers.py`, and `log_config` are gone; the package uses stdlib `logging`. `CROSSREF_API_BASE_URL` moved into `stavrophora.client`.
- `count()` no longer returns 0 on parse failures; it raises `ValidationError`.
- Models: envelope classes removed; entity models aligned with the live API (`LicenseRef.delay_in_days`, `FunderRef.doi_asserted_by`, `Work.score`/`source`/`journal_issue`/...).
- Settings: `max_requests_per_second` defaults to 3 and `max_concurrency` to 3 (polite-pool list limits, D-15); `secrets.env` is no longer read.

### Added

- Metadata Plus support: `plus_token=` / `STAVROPHORA_PLUS_TOKEN` sent as `crossref-api-key: Bearer <key>`.
- `WorksResource.facets(...)` returning `{facet_name: {value: count}}` and `WorksResource.sample(n)` (Crossref caps at 100).
- `WorksResource.batch_get_by_doi(dois) -> dict[str, Work]` (repeated `filter=doi:` keys, 50 per request).
- Scoped works routes for all parents: `members.works(id)`, `funders.works(id)`, `journals.works(issn)`, `prefixes.works(prefix)`, `types.works(type)`.
- Client-side guards for API 400s: route-unsupported parameters (`sort`/`select`/`filter`/`query` per route), `offset + rows > 10000`, cursor + date sorts, `sample(n) > 100`.
- Sixteen missing works filters (`gte-citation`/`lte-citation`, `project-id`, `ror-id`, event/approved/awarded dates, ...), `MemberFilters`, and `FunderFilters`.

### Fixed

- Integer ids are accepted everywhere an identifier goes: `members.get(297)`, scoped routes, and batch lookup keys no longer require a string.

### Migration from 0.2.1

| 0.2.1 | 0.3.0 |
|---|---|
| `async with StavrophoraSession(mailto=...) as session` | `async with StavrophoraClient(mailto=...) as client` |
| `resp = await session.works.search(search="q"); resp.message.items` | `page = await client.works.search(query="q"); page.results` |
| `search(filters, sort_by="issued:desc", page_size=50)` | `search(filters, sort="issued:desc", page_size=50)` |
| `client.journals.works(issn)` returning `ScopedWorksClient` | `client.journals.works(issn)` returning `ScopedWorksResource` (same methods, framework `Page`) |
| `session.works.iterate(page_size=100, on_validation_error=...)` | `client.works.iterate(page_size=1000, on_error="skip", failures=[])` |
| `from stavrophora.endpoints import WorksFilters` | `from stavrophora import WorksFilters` |
| `from stavrophora.models import ApiResponse` | `bibliofabric.Page` (deleted) |
| Plus token via `Crossref-Plus-API-Token` header (unimplemented) | `StavrophoraClient(plus_token=...)` sends `crossref-api-key: Bearer <key>` |

## [0.2.1] - 2026-10

### Fixed

- Crossref field parsing; aligned resource overrides with bibliofabric.

## [0.2.0] - 2026-09

### Added

- Crossref client, models, and resource clients on bibliofabric.
- Cursor/on_error/failures/on_page passthrough for `iterate`.
- Mocked test suite with pytest-httpx integration and live-api smoke tests.
- MkDocs documentation site and README.
- PyPI publishing via trusted publishing on release tags.

### Fixed

- Archive field parsed as a list of strings; prefix/member id URIs normalized.

### Changed

- Pinned dev `ty` and `ruff` versions; updated bibliofabric lock.

## [0.1.0] - 2026-08

### Added

- Project scaffold (uv, ruff, ty, CI).
