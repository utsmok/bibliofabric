# zenotheca: Project Guide

zenotheca is an async + generated-sync Python client for the Zenodo REST
API, built on bibliofabric 0.8. The name is final. The package is not yet
published on PyPI. Status alpha.

## Architecture

One generic framework layer (bibliofabric) plus a Zenodo-specific overlay.
Async I/O modules under `_async/` are the single source of truth;
`scripts/unasync.py --package zenotheca` generates the `_sync/` twins
(`ZenothecaSyncClient`, `ZenothecaRecordsSyncClient`, ...):

```
ZenothecaClient / ZenothecaSyncClient        # _async/client.py -> _sync/client.py
 |- records: ZenothecaRecordsClient          # _async/records.py (cached_property)
 |- communities: ZenothecaCommunitiesClient  # _async/communities.py (cached_property)
 |- vocabularies: VocabulariesClient         # _async/vocabularies.py (cached_property)
 `- oai: OaiClient                           # _async/oai.py (cached_property)
```

| File(s) | Role |
|---|---|
| `_async/client.py` | `ZenothecaClient(BaseApiClient)` on `https://zenodo.org/api` with `ZenothecaUnwrapper`; pins `Accept: application/json`. The framework sends the `User-Agent` Zenodo requires. `rate_class()` puts the two search routes in the `search` rate class. |
| `dialect.py`, `_async/dialect.py` | `ZENODO_DIALECT` (`size` max 25, `page` from 1, `q`, `sort`, `max_offset` 9,999), `ZENODO_DIALECT_AUTHED` (max 100), `dialect_for(api_token)`, `is_search_route(path, api_path)`, and `ZenothecaResourceClient` with the `with_params(all_versions=)` helper. |
| `_async/records.py` | `ZenothecaRecordsClient` (`path="records"`): `get()` follows redirects so concept ids answer the newest version; `versions()` lists a concept family; `latest()` follows the 301 of `versions/latest`; `files()` parses the full listing; `download_file()` streams `.../files/{key}/content` to disk (key is URL-quoted). `search`/`iterate`/`count` add `all_versions`. |
| `_async/communities.py` | `ZenothecaCommunitiesClient` (`path="communities"`): `search`/`get`/`iterate` on communities, plus `records()` searching the records of one community (`/communities/{slug}/records`) and `subcommunities()` listing the children of one community. |
| `_async/vocabularies.py` | `VocabulariesClient` (plain helper, not a `ResourceClient`): `search(name)`, `iterate(name)`, `get(name, id)` on `/vocabularies/{name}`; validates entries against `ZenothecaVocabulary`. |
| `_async/oai.py` | `OaiClient` for `https://zenodo.org/oai2d` (absolute URL, stdlib XML parsing): the six verbs plus `iterate_records`/`iterate_identifiers` following resumption tokens. `noRecordsMatch`/`noSetHierarchy` answer empty pages (OAI errors arrive as HTTP 422, caught via `APIError.response`), `idDoesNotExist` raises `NotFoundError`, the rest raise `ConfigurationError`. |
| `unwrapper.py` | `ZenothecaUnwrapper`: `hits.hits` results, `hits.total`, envelope minus `hits` as `Page.meta`, no cursors. |
| `filters.py` | Elasticsearch `q` clause builders (`term`, `phrase`, `community`, `resource_type`, `any_of`, `all_of`). |
| `ids.py` | `normalize_record_id` (bare id, `10.5281/zenodo.*` DOI, `/records/` URLs) and `normalize_community_slug`. |
| `config.py` | `ZenothecaSettings(BaseApiSettings)`, env prefix `ZENOTHECA_`, defaults 2 req/s, concurrency 5, and the rate class `search` at 0.5 req/s, cached `get_settings()`. |
| `models/` | Pydantic v2 models, `extra="allow"` everywhere; `ZenothecaRecord.links` values may be strings or nested objects. |
| `_sync/*.py` | Generated; never hand-edit. |

## Conventions

- Reads need no credentials. The optional `api_token` settings field
  (`ZENOTHECA_API_TOKEN`) sends `Authorization: Bearer` via
  `StaticTokenAuth` and selects `ZENODO_DIALECT_AUTHED` (page size 100,
  documented but unverified). Write routes remain out of scope.
- Zenodo rejects requests without a `User-Agent`; the framework's
  `effective_user_agent()` covers this. No other default headers.
- Unauthenticated page size caps at 25 (`ZENODO_MAX_PAGE_SIZE`); the
  Elasticsearch `max_result_window` of 10,000 caps deep paging and is
  checked client-side via `max_offset`.
- Verified record sorts: `bestmatch` (default), `mostrecent`, `-mostrecent`
  (`RECORD_SORT_OPTIONS`). `mostrecent` orders by last update.
- Rate limits (verified 2026-11-28, without a token): the two search
  routes (`/records` and `/communities/{slug}/records`) allow 30 requests
  per minute; every other route allows 133. The client paces the search
  routes in the `search` rate class at 0.5 req/s and everything else at
  2 req/s.
- Errors raise; 400/404 bodies are `{"status", "message"}` and surface as
  `APIError`/`NotFoundError` through the framework mapping.

## Development

Commands live at the workspace root. Package-specific bits: regenerate twins
with `uv run python scripts/unasync.py --package zenotheca`, offline suite
with `uv run pytest packages/zenotheca/tests`, live smoke tests with
`uv run pytest -m live_api packages/zenotheca/tests`. Live tests need no
credentials and download only one small file.

## Testing

`tests/_async/` is the source of truth (sync twin generated in
`tests/_sync/`, plus hand-written `tests/test_sync_in_event_loop.py`).
Fixtures in `tests/fixtures/` are trimmed real payloads (2026-11-27).
Offline tests use pytest-httpx and assert the outgoing request shape; live
tests carry the `live_api` marker.

## Known gaps

- Write routes (deposits, drafts, uploads, publishing) are unwrapped.
- `/api/vocabularies/funders` and `/api/vocabularies/affiliations` answer no
  entries; the client sends `funders`, `awards`, `affiliations`, and
  `subjects` to their top-level routes, which do. Unknown vocabulary names
  answer 404; `/api/names` answers 403.
- `/api/records/{id}/files-archive` (all files as one zip) answers 403
  without a token and is not wrapped; `download_file()` covers each file.
- Authenticated page size 100 is implemented but unverified (no token was
  available on 2026-11-27). The limits for token holders are unverified
  too; the `search` class applies to them as well.
