# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 0.3.0

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
