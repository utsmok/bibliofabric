# Stavrophora — Project Guide

## What It Is

Stavrophora is a Python client library for the [Crossref REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/), shipping an async client (`StavrophoraClient`) and a generated sync twin (`StavrophoraSyncClient`). It covers the works, journals, funders, members, types, prefixes, and licenses endpoints with typed Pydantic models. Built on **bibliofabric 0.6**, which owns HTTP, retries, per-class pacing, paging, and the generic `ResourceClient` / `SyncResourceClient`.

**Status:** Alpha. Published on PyPI as `stavrophora`. Current release: 0.3.0.

## Architecture

```
StavrophoraClient (_async/client.py, extends bibliofabric.BaseApiClient)
 ├─ generated sync twin: StavrophoraSyncClient (_sync/client.py, via scripts/unasync.py)
 ├─ resolves credentials: auth_strategy > plus_token (HeaderAuth) > mailto (QueryParameterAuth) > NoAuth
 │   (mailto is always propagated into settings so User-Agent carries mailto: even with plus_token)
 ├─ per-request-class pacing (D-19): top-level /works at 3 req/s ("list"), everything else at 10 req/s ("single"), 3 shared concurrent
 ├─ CrossrefUnwrapper (unwrapper.py): message / message.items / total-results / next-cursor
 └─ cached_property resources (_async/*.py + generated _sync/*.py), all on CrossrefResourceClient (_async/dialect.py):
     ├─ WorksResource        /works  (CrossrefDialect: cursor + rows=0 count; + batch_get_by_doi, facets, sample, agency, exists, latest_version)
     │    └─ ScopedWorksResource  /{parent}/{id}/works (full works list params; single-work methods guarded)
     │         └─ FunderWorksResource  /funders/{id}/works with include_descendants=True
     ├─ JournalsResource     /journals (CrossrefOffsetDialect; + dois_by_year, works)
     ├─ FundersResource      /funders  (CrossrefOffsetDialect; + descendants, works)
     ├─ MembersResource      /members  (CrossrefOffsetDialect; + works)
     ├─ TypesResource        /types    (single unpaged fetch for count/iterate; + works)
     ├─ PrefixesResource     /prefixes (no list route; search/count/iterate raise ConfigurationError)
     └─ LicensesResource     /licenses (CrossrefOffsetDialect; list/iterate only; get/exists raise ConfigurationError)
```

| Layer | File(s) | Role |
|-------|---------|------|
| Client | `_async/client.py` (`_sync/client.py`) | `StavrophoraClient(BaseApiClient)`; credential resolution; base URL `https://api.crossref.org/v1`; `rate_class()` split. |
| Dialect | `dialect.py`, `_async/dialect.py` | `CrossrefDialect` (works: `rows`/`offset`/`cursor`, `count_page_size=0`), `CrossrefOffsetDialect` (non-works: `cursor_param=None`, `count_page_size=0`), and `CrossrefResourceClient`: single `filter=` param with repeated-key OR, `sort="field:desc"` split & order validation, per-route capability checks, `offset + rows <= 10000` & `page >= 1` guards, cursor+date-sort rejection, `iterate()` defaulting to 1000 rows. |
| Resources | `_async/{works,journals,funders,members,types,prefixes,licenses}.py` | Per-route subclasses (with generated `_sync/*.py` twins): `path`, `model`, `filters_model`, `supports_*` flags, id normalization (`normalize_doi`, `normalize_issn`, `str(int)` ids). |
| Filters | `filters.py` | `WorksFilters` (full filter list with list/OR support), `MemberFilters`, `FunderFilters`; aliases to kebab-case wire names, `extra="allow"`. |
| Unwrapper | `unwrapper.py` | Crossref envelope → bibliofabric `Page` (`meta` = `message` minus `items`, so facets surface). |
| Models | `models/` | `base.py` shared types, `safe_types.py` (`IdSafeStr` strips `id.crossref.org` URIs), `work.py`, `entities.py`, `agency.py`. All `extra="allow"`. |
| Config | `config.py` | `StavrophoraSettings(BaseApiSettings)`, env prefix `STAVROPHORA_`; `mailto`, `plus_token`; per-class polite-pool pacing `{"single": 10.0, "list": 3.0}`, 3 concurrent (overridable via `rate_limits` or uniform `max_requests_per_second`). |

`ScopedWorksResource` gets its per-parent route through the core's `ResourceClient(client, path=...)` constructor argument.

## Tech Stack

- Python 3.12+, managed by the workspace `uv` setup
- **bibliofabric 0.6** (resolved from `packages/bibliofabric` in this workspace)
- **pydantic v2** + **pydantic-settings** for models and config
- **httpx** for async and sync HTTP (via bibliofabric); stdlib `logging`

## Project Structure

```
src/stavrophora/
  config.py, dialect.py, filters.py, unwrapper.py
  _async/                # single source of truth for I/O (client, dialect, resources)
  _sync/                 # generated sync twins (run scripts/unasync.py --package stavrophora)
  models/                # base, safe_types, work, entities, agency
tests/
  _async/                # pytest-httpx behavior suite + test_live_api.py
  _sync/                 # generated sync twins of tests/_async/
  fixtures/              # trimmed live payloads
  test_sync_event_loop.py
examples/                # runnable snippets against the public API
docs (workspace `docs/stavrophora/`)  # docs site pages (mkdocs build --strict must pass)
```

## Development Commands

Workspace commands live in the root `AGENTS.md`. Package-specific:

```bash
uv run python scripts/unasync.py --package stavrophora
uv run pytest packages/stavrophora/tests
STAVROPHORA_MAILTO=... uv run pytest packages/stavrophora/tests -m live_api
```

## Key Patterns & Conventions

- **Edit `_async/` only; never hand-edit `_sync/`.** Regenerate sync twins with `uv run python scripts/unasync.py --package stavrophora`.
- **Guards mirror API 400s and 404s.** Parameters or endpoints a route rejects raise `ConfigurationError` client-side; never send known-bad requests.
- **Models use `extra="allow"`** and tolerant types because the Crossref spec is incomplete and route shapes differ.
- **Filters serialize to one `filter` param**; list values are the repeated-key OR form.
- **Tests are behavior-focused** with pytest-httpx and trimmed real payloads from `tests/fixtures/`; no tests of private helpers or wiring tautologies.

## Known Issues & Gaps

- Metadata Plus auth is verified by construction only; no live Plus key was available.
- Live-verified quirks (rate limits, route gaps, paging caps) live in `docs/stavrophora/quirks.md` (workspace root).
