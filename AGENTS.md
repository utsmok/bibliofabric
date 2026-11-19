# Stavrophora — Project Guide

## What It Is

Stavrophora is an async Python client library for the [Crossref REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/). It wraps the works, journals, funders, members, types, prefixes, and licenses endpoints with typed Pydantic models, Crossref filter serialization, cursor pagination, and batch DOI lookup.

Built on top of **bibliofabric** — a generic async API client framework providing auth, pagination, response unwrapping, and resource operations.

**Status:** Alpha. Published on PyPI as `stavrophora`.

> **Migration note:** this repository is being migrated onto bibliofabric 0.6 (branch `overhaul-2026-11`). Sections marked below describe the pre-migration layout until Phase 2 lands.

## Architecture

```
StavrophoraSession       # User-facing async context manager (session.py)
 └─ StavrophoraClient    # Core HTTP client, auth resolution, resource orchestration (client.py)
     ├─ WorksClient           # includes batch_get_by_doi, agency, scoped works
     ├─ JournalsClient        # scoped works(issn)
     ├─ FundersClient         # scoped works(id)
     ├─ MembersClient
     ├─ TypesClient
     ├─ PrefixesClient        # scoped works(prefix); no /prefixes list route exists
     └─ LicensesClient
```

| Layer | File(s) | Role |
|-------|---------|------|
| **Session** | `session.py` | Thin async context manager around `StavrophoraClient`. Entry point for users. Delegates resource access via `__getattr__`. |
| **Client** | `client.py` | Extends `bibliofabric.BaseApiClient`. No auth required; optional `mailto` for the polite pool. |
| **Resources** | `resources/*.py` | Per-endpoint clients inheriting from `CrossrefResourceClient` (extends bibliofabric's base). Override paging/sort parameters for Crossref's `rows`/`offset`/`cursor` scheme. |
| **Endpoints** | `endpoints.py` | Pydantic filter models (`WorksFilters` etc.) with aliases for Crossref filter names. |
| **Unwrapper** | `unwrapper.py` | Extracts `message`, `message.items`, `total-results`, `next-cursor` from Crossref's JSON envelope. |
| **Config** | `config.py` | `StavrophoraSettings(BaseApiSettings)` via pydantic-settings. Env prefix `STAVROPHORA_`. Cached via `@lru_cache`. |
| **Constants** | `constants.py` | Base URL (`https://api.crossref.org/v1`), defaults, user-agent. |
| **Helpers** | `_helpers.py` | DOI/ISSN normalization, Crossref id handling. |
| **Models** | `models/` | `base.py` (envelope types), `safe_types.py` (`SafeStr`, `SafeStrList`), `work.py`, `entities.py`, `agency.py`. All use `extra="allow"` because the Crossref spec is incomplete. |

### Crossref conventions

- **Base URL**: `https://api.crossref.org/v1`
- **Auth**: none; `mailto=` query parameter opts into the polite pool (3 req/s vs 1 anonymous).
- **Paging**: `rows` (max 1000) + `offset` (capped at 10,000); deep paging uses `cursor`.
- **Filters**: repeated `filter=key:value` pairs are the OR form; the pipe form returns zero results.
- **Unknown query parameters get a 400**, so the client sends only known ones.

## Tech Stack

- **Python 3.12+**, `uv` for dependency management
- **bibliofabric 0.6** (git branch `overhaul-2026-11` until release)
- **pydantic v2** + **pydantic-settings** for models and config
- **httpx** for async HTTP (via bibliofabric)
- **pytest** + **pytest-asyncio** + **pytest-httpx** for testing
- **ruff** for linting/formatting, **ty** for type checking
- **mkdocs-material** + **mkdocstrings** for docs

## Project Structure

```
src/stavrophora/
  __init__.py           # Re-exports: client, session, __version__
  client.py             # StavrophoraClient (BaseApiClient subclass)
  session.py            # StavrophoraSession (user-facing async context manager)
  config.py             # StavrophoraSettings (pydantic-settings)
  constants.py          # Base URL, defaults, user-agent
  endpoints.py          # Filter models
  unwrapper.py          # CrossrefUnwrapper
  _helpers.py           # DOI/ISSN normalization helpers
  models/               # base, safe_types, work, entities, agency
  resources/            # per-endpoint clients
tests/                  # Phase 2 writes the new suite here
tests/_legacy/          # pre-migration suite, excluded from collection
```

## Development Commands

```bash
uv sync --locked --all-groups      # Install everything
uv run ruff check src tests        # Lint
uv run ruff format src tests       # Format
uv run ty check src                # Type check
uv run pytest                      # Run tests (legacy suite excluded)
uv build                           # Build package
uv run mkdocs serve                # Local docs
```

## Key Patterns & Conventions

- **All I/O is async.** Use `async with StavrophoraSession(mailto=...) as session:`.
- **Models use `extra="allow"`** everywhere to tolerate fields missing from the Crossref schema.
- **SafeStr/SafeStrList** normalize shapes that differ between list and single-item routes (e.g. journal `title` as string vs list).
- **Batch DOI lookup** uses repeated `filter=doi:` keys, 50 DOIs per request.
- **Scoped works** (`journals.works(issn)`, `funders.works(id)`, `prefixes.works(prefix)`) are methods on the respective resource clients.

## Known Issues & Gaps

- **Migration in progress**: the legacy test suite in `tests/_legacy/` is excluded from collection; a new suite arrives in Phase 2.
- **Live-verified quirks** (rate limits, route gaps, paging caps) are documented in the README.
