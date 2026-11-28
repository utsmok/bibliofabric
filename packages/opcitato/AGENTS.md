# opcitato: Project Guide

opcitato is a placeholder name. Rename the distribution name, the
import name, the environment prefix (`OPCITATO_`), the class prefix
(`Opcitato`), and the directories `packages/opcitato`,
`src/opcitato`, and `docs/opcitato` together.

opcitato is an async + generated-sync Python client for the
OpenCitations Index API v2 and Meta API v1, built on bibliofabric 0.8. Not
yet published.

## Architecture

```
OpcitatoClient / OpcitatoSyncClient   # _async/client.py -> _sync/client.py
 ├─ index                                             # _async/resources.py (cached_property)
 └─ meta                                              # _async/resources.py (cached_property)
```

| File(s) | Role |
|---|---|
| `_async/client.py` | `OpcitatoClient(BaseApiClient)`. No credentials. `default_headers` sends `Accept: application/json`. Exposes `index` and `meta` as cached properties. |
| `_async/resources.py` | `IndexClient` and `MetaClient`: one async method per API operation, shared `_row_params()` (require/filter/sort/format validation, repeated parameters URL-encoded into the path) and `_fetch_rows()`/`_fetch_count()` helpers. |
| `dialect.py` | Constants: the API base URL, the `index/v2` and `meta/v1` path prefixes, the `__` multi-id separator, the accepted formats, and the identifier scheme sets per API. |
| `ids.py` | `ParsedIdentifier(scheme, value)`, `parse_identifiers()` for the space-separated `citing`/`cited`/`id` strings, and the `normalize_*` validators that raise `ConfigurationError` for bare ids, whitespace, and unsupported schemes. |
| `csvparse.py` | `parse_csv_rows()` reads the `format=csv` tables; the CSV header repeats the JSON field names, so rows validate into the same models. |
| `unwrapper.py` | `OpcitatoUnwrapper`: top-level JSON list envelopes, `total` = list length, no cursor, no meta. |
| `_sync/*.py` | Generated sync twins from `_async/*.py`; never edit by hand. |
| `config.py` | `OpcitatoSettings(BaseApiSettings)`, env prefix `OPCITATO_`, `.env` support, `get_settings()` cached. Defaults: 3 requests per second (documented 180/min), concurrency 3. |
| `models/` | `Citation` (with `citing_identifiers`/`cited_identifiers` properties), `Count` (coerces the returned string to `int`), `MetadataRecord` (with `identifiers`, `authors`, `editors` properties), all `extra="allow"`, SafeStr fields. |

## Conventions

- Base URL `https://api.opencitations.net`, paths `index/v2/...` and
  `meta/v1/...`. No authentication; an OpenCitations Access Token would
  travel in an `authorization` header and is not managed yet.
- No paging anywhere. Every operation returns the complete result; repeated
  `require`/`filter` parameters travel in the query string of the path,
  because `BaseApiClient.request` types `params` as a mapping without
  repeated keys.
- An unknown identifier answers HTTP 200 with `[]`. Row methods return `[]`,
  count methods return `None`, `citation()` returns `None`.
- Counts arrive as strings (`{"count": "57"}`) and are coerced by `Count`.
- `creation` dates can be partial (`2013`, `2013-07`); `timespan` can be
  negative (`-P1Y1M16D`); `journal_sc`/`author_sc` are `"yes"`/`"no"`
  strings. All stay strings in the models.
- The client validates identifiers and row parameters before sending; the
  API's 400 answers (plain text body) surface as `APIError`.

## Development

Commands live at the workspace root (see the root `AGENTS.md`). Package
specifics: regenerate sync twins with `scripts/unasync.py --package
opcitato`, run the suite with `pytest packages/opcitato/tests`,
live tests with `-m live_api` (no credentials needed). The package is not a
uv workspace member until `pyproject.toml` lands; during development it is
imported through `.venv/lib/python3.12/site-packages/opcitato.pth`,
which points at `packages/opcitato/src` (the same pattern
zenotheca uses). Delete that file once the parent registers the package.

## Testing

`tests/_async/` is the source of truth (sync twin generated in
`tests/_sync/`, plus hand-written `tests/test_sync_in_event_loop.py`). Tests
without I/O live directly under `tests/` and run once. Offline tests
register responses with pytest-httpx (`add_response(json=...)`) without URL
matchers and assert the outgoing shape through `httpx_mock.get_requests()`;
CSV responses register `text=` with a `text/csv` content-type header. Real
trimmed payloads live in `tests/fixtures/`. `tests/_async/test_live_api.py`
(and `_sync`) carries the `live_api` marker; its ten tests send eleven
requests, drawn from the official documentation examples.

## Known gaps

- No Access Token support: anonymous usage is limited to 180 requests per
  minute per IP. Once a token exists, send it through `default_headers`.
- The `json=` transformation parameter (RAMOSE row reshaping, for example
  `json=array("; ",author)`) is not exposed; `params=` on the framework
  layer can send it, but the models do not expect reshaped rows.
- OpenCitations publishes full database dumps at download.opencitations.net
  for bulk harvesting; this client only covers the REST APIs.
