# rorifer: Project Guide

rorifer is an async + generated-sync Python client for the ROR API v2, built on bibliofabric 0.8. The name is final. The package is not yet published on PyPI.

## Architecture

One generic framework layer (bibliofabric) plus a ROR-specific overlay. Async I/O modules under `_async/` are the single source of truth; `scripts/unasync.py --package rorifer` generates the `_sync/` twins (`RoriferSyncClient`, `OrganizationsSyncClient`, `DumpsSyncClient`):

```
RoriferClient / RoriferSyncClient     # _async/client.py -> _sync/client.py
 ├─ organizations                    # _async/organizations.py -> _sync/organizations.py (cached_property)
 └─ dumps                            # _async/dumps.py -> _sync/dumps.py (cached_property)
```

| File(s) | Role |
|---|---|
| `_async/client.py` | `RoriferClient(BaseApiClient)`. No credentials. `default_headers` sends `Accept: application/json`. `rate_class()` puts requests to `zenodo.org` in the `zenodo` rate class. `heartbeat()` calls `GET /heartbeat` on the API host. Exposes `organizations` and `dumps` as cached properties. |
| `dialect.py` | Constants. `ROR_API_BASE_URL`, `ROR_HEARTBEAT_PATH`, the Zenodo base URL, host, community, and concept record id of the dumps, `ZENODO_SEARCH_PAGE_SIZE` (25), `ROR_PAGE_SIZE` (20), `ROR_MAX_PAGE` (500), the organization types, the record statuses, the eight filter keys, and `ROR_DIALECT` (no page-size parameter, no sort, no select, `page` from 1, `max_offset` 9980). |
| `_async/dialect.py` | `RoriferResourceClient[E]`: one `filter=key:value` parameter (`serialize_filter_params`), bare-id normalization (accepts the bare id, `https://ror.org/<id>`, and `ror.org/<id>`), and `exists()` through `GET` because `HEAD` answers 403. `with_query_options()` merges `query.advanced` and `all_status`. |
| `_async/organizations.py` | `OrganizationsClient`. `search`, `iterate`, `count`, `collect`, and `first` gain `advanced=` and `all_status=` and raise `ConfigurationError` for `page_size=`. Adds `match_affiliation`, `find_by_external_id` (exact `external_ids.all` phrase through `query.advanced`, `id_type` applied client-side), and `find_by_funder_doi`. |
| `_async/dumps.py` | `DumpsClient`: `list(limit=)` reads the Zenodo search with `all_versions=true` and pages by 25; `latest()` reads the concept record and follows its redirect to the newest release; `download(dump, dest)` streams the zip to disk. |
| `_sync/*.py` | Generated sync twins from `_async/*.py`; never edit by hand. |
| `filters.py` | `OrganizationFilters` with dot-notation aliases and `extra="allow"`; `external_id_query()` builds the `query.advanced` clause for one external id. |
| `unwrapper.py` | `RoriferUnwrapper`: `items`, `number_of_results`, facets into `Page.meta`, `ConfigurationError` on an `errors` envelope, and `APIError` on a body of another shape. |
| `config.py` | `RoriferSettings(BaseApiSettings)`, env prefix `RORIFER_`, `.env` support, `get_settings()` cached. Defaults: 6 requests per second, concurrency 5, and the rate class `zenodo` at 0.5 requests per second. |
| `dump.py` | Pure functions. `iter_dump_records(path)` reads the JSON member of a dump zip one record at a time; `index_external_ids(records, id_type)`; `compact_external_id(value)`. |
| `crosswalk.py` | `fundref_id_from_doi` and `fundref_doi_from_id` for the Crossref Funder Registry prefix `10.13039/`. |
| `models/` | Pydantic v2 models (`Organization`, `AffiliationMatch`, `RorDump`, and their parts), `extra="allow"`, SafeList/SafeStr from bibliofabric. |

## Conventions

- Base URL `https://api.ror.org/v2`. No authentication. Dumps come from `https://zenodo.org/api`.
- Pages hold 20 records, pages 1 to 500. No sort, select, cursor, or page size. A query that needs page 501 raises `ConfigurationError`; it does not stop quietly.
- A rejected request answers HTTP 200 with `{"errors": [...]}` and raises `ConfigurationError`. A body without an `items` list raises `APIError`.
- `query` and `query.advanced` cannot be combined.
- Filters: one `filter=key:value` parameter; a list value repeats the key (OR); keys are joined with commas (AND).
- Only active records answer a search unless `all_status=True`.
- Rate limits: ROR documents 2,000 requests per 5 minutes per IP address. The anonymous Zenodo search accepts 30 requests per minute and 25 records per page.
- No sessions, no loguru: stdlib logging throughout.

## Development

Commands live at the workspace root (see the root `AGENTS.md`). Package-specific bits: regenerate sync twins with `uv run python scripts/unasync.py --package rorifer`, run the suite with `uv run pytest packages/rorifer/tests`, and run the live tests with `uv run pytest -m live_api packages/rorifer/tests` (no credentials needed).

## Testing

`tests/_async/` is the source of truth (sync twin generated in `tests/_sync/`, plus hand-written `tests/test_sync_in_event_loop.py`). Tests without I/O live directly under `tests/` and run once (`test_dump_reader.py`, `test_crosswalk.py`, `test_settings.py`). Tests use pytest-httpx: responses are registered with `add_response(json=...)`, and the outgoing shape is asserted through `httpx_mock.get_requests()`. Real payload fixtures live in `tests/fixtures/`. `tests/_async/test_live_api.py` (and `_sync`) carries the `live_api` marker; one of its tests downloads the real dump (about 41 MB) and parses all records.

## Known gaps

- ROR sends no rate-limit headers and registration for API client ids is paused; once it opens, add the client id through `default_headers`.
- The API cannot OR two different filter keys, and it reaches at most 10,000 records per query. Use the dump for complete lists.
- `external_ids.all` cannot be searched for a value that contains a double quote, a backslash, or a colon.
