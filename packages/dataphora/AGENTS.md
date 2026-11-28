# dataphora: Project Guide

dataphora is an async + generated-sync Python client for the DataCite
REST API (https://api.datacite.org), built on bibliofabric 0.8. The name is
final. Status alpha, not yet published on PyPI.

## Architecture

Async I/O modules under `_async/` are the single source of truth;
`scripts/unasync.py --package dataphora` generates the `_sync/` twins
(`DataphoraSyncClient`, `DoisSyncClient`, and so on):

```
DataphoraClient / DataphoraSyncClient    # _async/client.py -> _sync/client.py
 ├─ dois, activities                          # _async/dois.py -> _sync/dois.py
 ├─ clients, client_prefixes                  # _async/registry.py -> _sync/registry.py
 ├─ providers, provider_prefixes
 ├─ repositories, prefixes
 ├─ events                                    # _async/events.py -> _sync/events.py
 └─ graphql                                   # _async/graphql.py -> _sync/graphql.py
```

| File(s) | Role |
|---|---|
| `_async/client.py` | `DataphoraClient(BaseApiClient)` with `JsonApiUnwrapper(cursor_param="page[cursor]")`, `Accept: application/vnd.api+json`, cached resource properties. No credentials, ever. |
| `dialect.py`, `_async/dialect.py` | `DATACITE_DIALECT` (`page[size]`, `page[number]`, `page[cursor]` start `"1"`, `sort`, `query`, `fields[dois]`, max page size 1000) and `dialect_with()` to re-point `select_param` per resource. `DataphoraResourceClient` serializes filters as one query parameter per criterion with comma-joined sequence values; `DataphoraDoiClient` normalizes DOI ids with `bibliofabric.ids.normalize_doi`. |
| `filters.py` | `DoiFilters`, `ClientFilters`, `ProviderFilters`, `RepositoryFilters`, `PrefixFilters`, `EventFilters` with hyphenated aliases, plus `serialize_filter_params()` (sequences join with commas, booleans lowercase). |
| `models/common.py` | `DataphoraResource` flattens the JSON:API envelope in a before-validator (attributes merge into the top level, `relationships` and `links` kept); `JsonApiRelationship`/`JsonApiIdentifier`; `resource_ids()`. |
| `models/doi.py` | `DataphoraDoi` with the full attribute set, helpers `title`, `resource_type`, `client_id`, `provider_id`; string affiliations and string-or-object publishers are coerced. |
| `models/registry.py` | `DataphoraClientRecord` (named to avoid the `*Client` sync-rename collision), `DataphoraProvider`, `DataphoraRepository`, `DataphoraPrefix`, `DataphoraClientPrefix`, `DataphoraProviderPrefix`, `DataphoraEvent` (hyphenated attribute aliases), `DataphoraActivity`, `DataphoraTotals`, `Issn`, `FacetCount`. |
| `_async/dois.py` | `DoisClient` (`/dois`, `activities()`) and `ActivitiesClient` (global `/activities`). |
| `_async/registry.py` | `ClientsClient`, `ProvidersClient`, `RepositoriesClient`, `PrefixesClient` (each with `dois()` and, for the first, second, and fourth, `totals()`), `ClientPrefixesClient`, `ProviderPrefixesClient`. `PrefixesClient.totals()` handles the `204 No Content` anonymous answer. |
| `_async/events.py` | `EventsClient`. |
| `_async/graphql.py` | `GraphqlClient.query()`: one `POST /graphql` per query with `retry=True`; returns the `data` object unvalidated and raises `APIError` (body attached) for a rejected query (400) or a failed field (200 with `errors`). Queries only; mutations need a token. |

## Conventions

- Base URL `https://api.datacite.org`. Envelope is JSON:API 1.0; the
  unwrapper reads totals from `meta.total` and cursors from `links.next`.
- Filters travel as one query parameter per criterion. The API silently
  ignores unknown parameters, so the filter models are the safety net.
- `iterate()` walks `page[cursor]` (no depth limit, `created` ascending);
  `search()` defaults to numbered paging, capped at 10,000 records upstream.
- Settings: `DataphoraSettings`, env prefix `DATAPHORA_`, 1.5 req/s and
  concurrency 3 by default (documented anonymous limit: 500 requests per
  5 minutes, no rate-limit headers are sent).
- No login routes are wrapped; see `docs/dataphora/upstream-quirks.md`.

## Development

Commands live at the workspace root (see the root `AGENTS.md`). The package
is a workspace member with its own `pyproject.toml`. Package-specific bits:
regenerate twins with `uv run python scripts/unasync.py --package
dataphora`, run the offline suite with `uv run pytest
packages/dataphora/tests`, and run the live tests with `uv run pytest -m
live_api packages/dataphora/tests`. Live tests need no credentials.

## Testing

`tests/_async/` is the source of truth (sync twin generated in
`tests/_sync/`, plus hand-written `tests/test_sync_in_event_loop.py`).
pytest-httpx carries the responses; request-shape tests assert the bracketed
parameter names (`page[size]`, `page[cursor]`, `fields[dois]`). Real
payloads trimmed to one record live in `tests/fixtures/`. Offline settings
and model tests sit directly under `tests/` so they run once.
