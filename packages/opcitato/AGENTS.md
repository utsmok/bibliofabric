# opcitato: Project Guide

opcitato is an async + generated-sync Python client for the
OpenCitations Index API v2, the Meta API v1, and the SPARQL endpoint of
each dataset, built on bibliofabric 0.8. The name is final. The package
is not yet published on PyPI.

## Architecture

```
OpcitatoClient / OpcitatoSyncClient   # _async/client.py -> _sync/client.py
 ├─ index                                             # _async/resources.py (cached_property)
 └─ meta                                              # _async/resources.py (cached_property)
```

| File(s) | Role |
|---|---|
| `_async/client.py` | `OpcitatoClient(BaseApiClient)`. No credentials. `default_headers` sends `Accept: application/json`. Exposes `index` and `meta` as cached properties. |
| `_async/resources.py` | `IndexClient` and `MetaClient`: one async method per API operation, shared `_row_params()` (require/filter/sort/format validation, repeated parameters URL-encoded into the path), the `_fetch_rows()`/`_fetch_count()` helpers, and `sparql()`/`sparql_text()` through `_send_sparql()`. |
| `dialect.py` | Constants: the API base URL, the `index/v2` and `meta/v1` path prefixes, the two SPARQL endpoint URLs, the `__` multi-id separator, the accepted formats, and the identifier scheme sets per API. |
| `ids.py` | `ParsedIdentifier(scheme, value)`, `parse_identifiers()` for the space-separated `citing`/`cited`/`id` strings, and the `normalize_*` validators that raise `ConfigurationError` for bare ids, whitespace, and unsupported schemes and return the identifier percent-encoded for the URL path. |
| `csvparse.py` | `parse_csv_rows()` reads the `format=csv` tables; the CSV header repeats the JSON field names, so rows validate into the same models. |
| `unwrapper.py` | `OpcitatoUnwrapper`: top-level JSON list envelopes, `total` = list length, no cursor, no meta. The resource clients read responses directly; the unwrapper satisfies the `BaseApiClient` constructor. |
| `_sync/*.py` | Generated sync twins from `_async/*.py`; never edit by hand. |
| `config.py` | `OpcitatoSettings(BaseApiSettings)`, env prefix `OPCITATO_`, `.env` support, `get_settings()` cached. Defaults: 3 requests per second (documented 180/min), concurrency 3. |
| `models/` | `Citation` (with `citing_identifiers`/`cited_identifiers` properties), `Count` (coerces the returned string to `int`), `MetadataRecord` (with `identifiers`, `authors`, `editors` properties), `SparqlResult` (with `rows()`), all `extra="allow"`, SafeStr fields where the API answers strings. |

## Conventions

- Base URL `https://api.opencitations.net`, paths `index/v2/...` and
  `meta/v1/...`. The SPARQL endpoints live on
  `https://sparql.opencitations.net/index` and `/meta` and are called with
  absolute URLs through the same client, so they share the limiter. No
  authentication; the optional Access Token would travel in an
  `authorization` header and is not managed.
- No paging anywhere. Every operation returns the complete result; repeated
  `require`/`filter` parameters travel in the query string of the path,
  because `BaseApiClient.request` types `params` as a mapping without
  repeated keys.
- An unknown identifier answers HTTP 200. Row operations answer `[]` and
  return `[]`; `citation()` returns `None`. The count operations answered a
  zero row (`[{"count": "0"}]`) on 2026-11-28 and `[]` on 2026-11-27, so
  `citation_count()` and friends return `0` or `None`.
- Counts arrive as strings (`{"count": "57"}`) and are coerced by `Count`.
- A JSON body that is not a list raises `ConfigurationError`; a row that
  fails its model raises `bibliofabric.ValidationError`.
- `creation` dates can be partial (`2013`, `2013-07`); `timespan` can be
  negative (`-P1Y1M16D`); `journal_sc`/`author_sc` are `"yes"`/`"no"`
  strings. All stay strings in the models.
- The client validates identifiers and row parameters before sending; the
  API's 400 answers (plain text body) surface as `APIError`.

## Development

Commands live at the workspace root (see the root `AGENTS.md`). Package
specifics: regenerate sync twins with `scripts/unasync.py --package
opcitato`, run the suite with `pytest packages/opcitato/tests`, and run
the live tests with `-m live_api` (no credentials needed).

## Testing

`tests/_async/` is the source of truth (sync twin generated in
`tests/_sync/`, plus hand-written `tests/test_sync_in_event_loop.py`). Tests
without I/O live directly under `tests/` and run once. Offline tests
register responses with pytest-httpx (`add_response(json=...)`) without URL
matchers and assert the outgoing shape through `httpx_mock.get_requests()`;
CSV responses register `text=` with a `text/csv` content-type header. Real
trimmed payloads live in `tests/fixtures/`, one file per registered
response. `tests/_async/test_live_api.py` (and `_sync`) carries the
`live_api` marker; its fifteen tests send eighteen requests, drawn from the
official documentation examples.

## Known gaps

`docs/roadmap/deferred.md` lists what the package leaves out, with the
reason and the unblock condition. In short:

- The Access Token is optional, free, and does not change the rate limit.
  The client sends none.
- The `json=` transformation parameter (for example
  `json=array("; ",author)`) reshapes rows and is not exposed.
- The legacy Index API v1 and the database dumps at
  download.opencitations.net are not wrapped.
