# hodoi: Project Guide

hodoi is a placeholder name. Rename the distribution name, the import name, the environment prefix (`HODOI_`), the class prefix (`Hodoi`), and the directories `packages/hodoi`, `src/hodoi`, and `docs/hodoi` together.

hodoi is an async + generated-sync Python client for the DOI System proxy server at doi.org, built on bibliofabric 0.8. Not yet published.

## Architecture

Unlike the resource-based clients, this package is one flat client: doi.org has three small routes and no paging, so `HodoiClient` carries every method itself. Async I/O modules under `_async/` are the single source of truth; `scripts/unasync.py --package hodoi` generates the `_sync/` twins:

```
HodoiClient / HodoiSyncClient     # _async/client.py -> _sync/client.py
```

| File(s) | Role |
|---|---|
| `_async/client.py` | `HodoiClient(BaseApiClient)`. No credentials, no `default_headers` override (the `Accept` header is per request because it selects the representation). Methods: `agencies`/`agency`, `handle`, `landing_url`, `content`, `raw`. `content()` sends `follow_redirects=True`; everything else keeps the settings default (off) so callers can inspect the resolver's 302. |
| `dialect.py` | `DOI_BASE_URL`, `RA_BATCH_SIZE` (100), `normalize_doi()` (validating; strips `https://doi.org/`, `dx.doi.org`, `doi:`, `info:doi:` wrappers), `strip_doi_form()` (wrapper stripping only, used by `agencies()` because `/ra/` answers malformed strings itself). |
| `media_types.py` | The catalog: `CSL_JSON`, `DATACITE_JSON`, `DATACITE_XML`, `SCHEMAORG_JSONLD`, `UNIXREF_XML`, `UNIXSD_XML`, `ONIX_DOI_XML`, `BIBTEX`, `RIS`, `BIBLIOGRAPHY`, `RDF_XML`, `TURTLE`, plus `JSON_MEDIA_TYPES` and `AGENCY_SUPPORT`. |
| `config.py` | `HodoiSettings` (prefix `HODOI_`): timeout 60 s, 2 req/s, concurrency 2, `follow_redirects` off. |
| `unwrapper.py` | `HodoiUnwrapper`, a minimal `ResponseUnwrapper`; the client reads responses directly, so this only satisfies the `BaseApiClient` constructor. |
| `models/` | `AgencyAnswer` (`DOI`, `RA`, `status`), `HandleRecord`/`HandleValue`/`HandleValueData`/`HandleAdminValue`, `CslItem`, `DataciteRecord`, `SchemaOrgThing`; all `extra="allow"`. |

## Conventions

- Base URL `https://doi.org`. No authentication, no paging.
- DOI inputs accept the bare name and the URL forms; `normalize_doi()` raises `ConfigurationError` for anything else.
- `/ra/` answers HTTP 200 for unknown (`DOI does not exist`), malformed (`Invalid DOI`), and unknown-prefix (`Unknown`) DOIs; `AgencyAnswer.status` carries the string. `handle()` raises `NotFoundError` (HTTP 404).
- `content()` raises `APIError` with the agency's HTTP 406 body for media types the agency does not serve.
- No sessions, no loguru: stdlib logging throughout.

## Development

Commands live at the workspace root (see the root `AGENTS.md`). Package-specific bits: regenerate sync twins with `uv run python scripts/unasync.py --package hodoi`, run the suite with `uv run pytest packages/hodoi/tests`, and run the live tests with `uv run pytest -m live_api packages/hodoi/tests` (no credentials needed).

## Testing

`tests/_async/` is the source of truth (sync twin generated in `tests/_sync/`, plus hand-written `tests/test_sync_in_event_loop.py`). Tests without I/O live directly under `tests/` (`test_settings.py`, `test_media_types.py`). Tests use pytest-httpx: responses are registered with `add_response(json=...)` or `text=...` without URL matchers, and the outgoing shape is asserted through `httpx_mock.get_requests()`. Real payload fixtures (trimmed, 2026-11-27) live in `tests/fixtures/`. `tests/_async/test_live_api.py` (and `_sync`) carries the `live_api` marker.

## Known gaps

- doi.org publishes no rate limit; 2 req/s is a courtesy default, not a documented cap.
- Only Crossref, DataCite, and mEDRA were verified live. Other agencies (EIDR, JaLC, etc.) answer `/ra/` with their names but their content negotiation and handle records were not exercised.
- The resolver's multi-URL features (`10320/loc` values, `noredirect`, `urlappend`, `locatt`) are not modeled; `handle()` exposes the raw record.
- `HS_SITE` and `HS_VLIST` value shapes pass through as extra fields; the client types only `string`, `base64`/`hex` (as strings), and `admin` data.
