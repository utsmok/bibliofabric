# Stavrophora — Project Guide

## What It Is

Stavrophora is an async Python client library for the [Crossref REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/). It covers the works, journals, funders, members, types, prefixes, and licenses endpoints with typed Pydantic models. Built on **bibliofabric 0.6**, which owns HTTP, retries, pacing, paging, and the generic `ResourceClient`.

**Status:** Alpha. Published on PyPI as `stavrophora`. Current release: 0.3.0.

## Architecture

```
StavrophoraClient (client.py, extends bibliofabric.BaseApiClient)
 ├─ resolves credentials: auth_strategy > plus_token (HeaderAuth) > mailto (QueryParameterAuth) > NoAuth
 ├─ CrossrefUnwrapper (unwrapper.py): message / message.items / total-results / next-cursor
 └─ cached_property resources (resources/), all on CrossrefResourceClient (dialect.py):
     ├─ WorksResource        /works  (+ batch_get_by_doi, facets, sample, agency)
     │    └─ ScopedWorksResource  /{parent}/{id}/works, per-instance path
     ├─ JournalsResource     /journals
     ├─ FundersResource      /funders
     ├─ MembersResource      /members
     ├─ TypesResource        /types
     ├─ PrefixesResource     /prefixes (no list route; search/count/iterate raise)
     └─ LicensesResource     /licenses (list/iterate only)
```

| Layer | File(s) | Role |
|-------|---------|------|
| Client | `client.py` | `StavrophoraClient(BaseApiClient)`; credential resolution; base URL `https://api.crossref.org/v1`. |
| Dialect | `dialect.py` | `CrossrefDialect` (`rows`/`offset`/`cursor`, no `page`) and `CrossrefResourceClient`: single `filter=` param with repeated-key OR, `sort="field:desc"` split into `sort`/`order`, per-route capability checks, `offset + rows <= 10000` guard, cursor+date-sort rejection, `iterate()` defaulting to 1000 rows. |
| Resources | `resources/*.py` | Per-route subclasses: `path`, `model`, `filters_model`, `supports_*` flags, id normalization (`normalize_doi`, `normalize_issn`, `str(int)` ids). |
| Filters | `filters.py` | `WorksFilters` (full filter list), `MemberFilters`, `FunderFilters`; aliases to kebab-case wire names, `extra="allow"`. |
| Unwrapper | `unwrapper.py` | Crossref envelope → bibliofabric `Page` (`meta` = `message` minus `items`, so facets surface). |
| Models | `models/` | `base.py` shared types, `safe_types.py` (`IdSafeStr` strips `id.crossref.org` URIs), `work.py`, `entities.py`, `agency.py`. All `extra="allow"`. |
| Config | `config.py` | `StavrophoraSettings(BaseApiSettings)`, env prefix `STAVROPHORA_`; `mailto`, `plus_token`; polite-pool pacing 3/s, 3 concurrent. |

`ScopedWorksResource` gets its per-parent route through the core's `ResourceClient(client, path=...)` constructor argument.

## Tech Stack

- Python 3.12+, managed by the workspace `uv` setup
- **bibliofabric 0.6** (resolved from `packages/bibliofabric` in this workspace)
- **pydantic v2** + **pydantic-settings** for models and config
- **httpx** for async HTTP (via bibliofabric); stdlib `logging`

## Project Structure

```
src/stavrophora/
  client.py, config.py, dialect.py, filters.py, unwrapper.py
  models/                # base, safe_types, work, entities, agency
  resources/             # works (+scoped), journals, funders, members, types, prefixes, licenses
tests/                   # pytest-httpx behavior suite; fixtures/ = trimmed live payloads
tests/test_live_api.py   # live_api-marked smoke tests, deselected by default
examples/                # runnable snippets against the public API
docs (workspace `docs/stavrophora/`)  # docs site pages (mkdocs build --strict must pass)
```

## Development Commands

Workspace commands live in the root `AGENTS.md`. Package-specific: the suite
is `packages/stavrophora/tests`, and live smoke tests need
`STAVROPHORA_MAILTO=... uv run pytest -m live_api`.

## Key Patterns & Conventions

- **All I/O is async.** `async with StavrophoraClient(mailto=...) as client:`.
- **Guards mirror API 400s.** Parameters a route rejects (per its swagger) raise `ConfigurationError` client-side; never send known-bad requests.
- **Models use `extra="allow"`** and tolerant types because the Crossref spec is incomplete and route shapes differ.
- **Filters serialize to one `filter` param**; list values are the repeated-key OR form.
- **Tests are behavior-focused** with pytest-httpx and trimmed real payloads from `tests/fixtures/`; no tests of private helpers or wiring tautologies.

## Known Issues & Gaps

- Pacing is a flat 3 requests/s; Crossref's 2026-07 split allows 10/s for single records. A request-class-aware limiter is a core change request, not yet implemented (see the phase 2 migration report).
- Metadata Plus auth is verified by construction only; no live Plus key was available.
- Live-verified quirks (rate limits, route gaps, paging caps) live in `docs/stavrophora/quirks.md` (workspace root).
