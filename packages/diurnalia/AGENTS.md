# diurnalia: Project Guide

diurnalia is an async + generated-sync Python client for the DOAJ (Directory of Open Access Journals) API v4, built on bibliofabric 0.8. Not yet published.

## Architecture

One generic framework layer (bibliofabric) plus a DOAJ-specific overlay. Async I/O modules under `_async/` are the single source of truth; `scripts/unasync.py --package diurnalia` generates the `_sync/` twins (`DiurnaliaSyncClient`, `JournalsSyncClient`, `ArticlesSyncClient`):

```
DiurnaliaClient / DiurnaliaSyncClient   # _async/client.py -> _sync/client.py
 ├─ journals                         # _async/journals.py -> _sync/journals.py (cached_property)
 └─ articles                         # _async/articles.py -> _sync/articles.py (cached_property)
```

| File(s) | Role |
|---|---|
| `_async/client.py` | `DiurnaliaClient(BaseApiClient)`. No credentials. Base URL `https://doaj.org/api/v4`. `default_headers` sends `Accept: application/json`. Exposes `journals` and `articles` as cached properties. |
| `dialect.py` | Constants and `DOAJ_DIALECT`: `page` from 1, `pageSize` clamped to 50 (default 10), `max_offset` 999, `sort` supported, no query parameter (the query lives in the path), no cursor, no select. |
| `_async/base.py` | `DiurnaliaResourceClient[E]`: `search_path()` encodes the query into the path (`/search/journals/{query}`, match-all `*` when absent) and `exists()` runs the search route because there is no id route. |
| `_async/journals.py` | `JournalsClient[Journal]`. `get(issn)` searches `issn:<normalized>` and raises `NotFoundError` on zero results. |
| `_async/articles.py` | `ArticlesClient[Article]`. `get(doi)` searches `doi:<normalized>` and raises `NotFoundError` on zero results. |
| `_sync/*.py` | Generated sync twins from `_async/*.py`; never edit by hand. |
| `filters.py` | `issn_query()` and `doi_query()` build the fielded clauses; both normalize through `bibliofabric.ids`. |
| `unwrapper.py` | `DiurnaliaUnwrapper`: `results`, `total`, and the envelope rest into `Page.meta`. Pages carry `next`/`prev` as URLs, so there is no cursor. |
| `config.py` | `DiurnaliaSettings(BaseApiSettings)`, env prefix `DIURNALIA_`, `.env` support, `get_settings()` cached. Defaults: 1 request per second, concurrency 2 (DOAJ documents a limit of 2 per second with bursts of 5). |
| `models/` | Pydantic v2 models (`Journal`, `Article`, and their `bibjson` parts), `extra="allow"`, SafeList/SafeStr from bibliofabric. |

## Conventions

- Every read goes through a search route; DOAJ has no listing route. One query reaches at most 1000 records (`(page - 1) * pageSize + pageSize <= 1000`); the client raises `ConfigurationError` beyond that.
- `pageSize` values above 50 are clamped by the API itself; the dialect already caps the parameter at 50.
- A query that matches nothing answers 200 with `total: 0`; `get()` turns that into `NotFoundError`.
- Rejected queries (bad sort field, wildcards, fuzzy or regex syntax) answer 400 and raise `APIError`.
- No sessions, no loguru: stdlib logging throughout.

## Development

Commands live at the workspace root (see the root `AGENTS.md`). Package-specific bits: regenerate sync twins with `uv run python scripts/unasync.py --package diurnalia`, run the suite with `uv run pytest packages/diurnalia/tests`, and run the live tests with `uv run pytest -m live_api packages/diurnalia/tests` (no credentials needed).

## Testing

`tests/_async/` is the source of truth (sync twin generated in `tests/_sync/`, plus hand-written `tests/test_sync_in_event_loop.py`). Tests without I/O live directly under `tests/` and run once (`test_models.py`, `test_queries.py`, `test_settings.py`). Tests use pytest-httpx: responses are registered with `add_response(json=...)` without URLs, and the outgoing path (query in the path, decoded by `last_path()`) and params are asserted through `httpx_mock.get_requests()`. Real payload fixtures live in `tests/fixtures/`. `tests/_async/test_live_api.py` (and `_sync`) carries the `live_api` marker and hits the real search routes.

## Known gaps

- The API serves at most 1000 records per query. Full harvests should use the DOAJ public data dump (https://doaj.org/docs/public-data-dump/), which this package does not read.
- Applications search (`/api/v4/search/applications/`) needs an admin API key and is not wrapped.
- Write routes (article and application CRUD, bulk uploads, journal management) need an admin key and are not wrapped.
- Wildcards, fuzzy (`~`), regex, and proximity syntax are disabled by DOAJ; a query using them answers 400.
