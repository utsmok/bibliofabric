# scholiast: Project Guide

scholiast is an async + generated-sync Python client for the
Semantic Scholar Academic Graph, Recommendations, and Datasets APIs, built
on bibliofabric 0.8. Not yet published.

## Architecture

One generic framework layer (bibliofabric) plus a Semantic Scholar
overlay. Async I/O modules under `_async/` are the single source of truth;
`scripts/unasync.py --package scholiast` generates the `_sync/`
twins (`ScholiastSyncClient`, `PapersSyncClient`,
`AuthorsSyncClient`, and so on):

```
ScholiastClient / ScholiastSyncClient
 ├─ papers            # _async/papers.py -> _sync/papers.py (cached_property)
 ├─ authors           # _async/authors.py -> _sync/authors.py (cached_property)
 ├─ recommendations   # own base URL /recommendations/v1
 ├─ datasets          # own base URL /datasets/v1
 ├─ snippets          # /snippet/search, needs a key upstream
 └─ patents           # /patent routes
```

| File(s) | Role |
|---|---|
| `_async/client.py` | `ScholiastClient(BaseApiClient)`. Base URL is the graph API; recommendations and datasets pass absolute URLs. `default_headers` sends `x-api-key` when the settings carry a key. |
| `dialect.py` | Constants: the three base URLs, `SEMANTICSCHOLAR_DIALECT` (`limit` page size up to 100, `offset` paging capped at 9900, `query` param, `fields` select), batch limits (500 papers, 1000 authors), bulk-search limit (1000). |
| `_async/resources.py` | `ScholiastResourceClient[E]`: ids travel verbatim, `exists()` uses `GET` (the gateway answers `HEAD` with 405), and `fetch_list_page()` reads the `{data, next, offset}` envelopes of the sub-list routes. |
| `_async/papers.py` | `PapersClient`. `search_path` is `paper/search`; `search()` adds `fields=`; `batch_get` is disabled in favor of `batch()` (POST, chunked at 500, nulls dropped, `retry=True`); `bulk_search`/`bulk_iterate` page by token; `citations`, `references`, `authors` are offset-paged pages. |
| `_async/authors.py` | `AuthorsClient`. `search_path` is `author/search`; `papers()` page; `batch()` POST chunked at 1000 with nulls dropped. |
| `_async/recommendations.py` | `RecommendationsClient`: `for_paper()` GET and `for_list()` POST (`retry=True`) against `/recommendations/v1`; both read `recommendedPapers`. |
| `_async/datasets.py` | `DatasetsClient` against `/datasets/v1`: `releases()` (plain string array), `release()`/`latest()`, `dataset()` (key-gated), `diffs()` (key-gated). |
| `_async/snippets.py` | `SnippetsClient.search()` on `/snippet/search` (key-gated upstream). |
| `_async/patents.py` | `PatentsClient`: `get()` by UCID, `search()` and `outbound_citations()` pages. |
| `_sync/*.py` | Generated sync twins from `_async/*.py`; never edit by hand. |
| `filters.py` | `PaperSearchFilters` with `extra="allow"`; each criterion becomes its own query parameter. |
| `unwrapper.py` | `ScholiastUnwrapper`: `data`/`matches`/`recommendedPapers` result lists, `total`, `next` offset or bulk `token` as the cursor, and the envelope minus the results as `Page.meta`. |
| `config.py` | `ScholiastSettings(BaseApiSettings)`, env prefix `SCHOLIAST_`, optional `api_key` (`SecretStr`), defaults 1 request per second and concurrency 1, `get_settings()` cached. |
| `models/` | Pydantic v2 models (`Paper`, `Author`, `Citation`, `Reference`, `SnippetMatch`, `Patent`, `Release`, and their parts), `extra="allow"`, SafeList/SafeStr from bibliofabric. The datasets models keep the API's snake_case names. |

## Conventions

- Base URLs: `https://api.semanticscholar.org/graph/v1`,
  `/recommendations/v1`, `/datasets/v1`.
- Optional key, sent as the `x-api-key` header. Published limits: 1000
  req/s shared for the anonymous pool, 1 req/s guaranteed per key. The
  client defaults to 1 req/s, concurrency 1.
- The shared pool throttles unevenly; any keyless request can answer 429.
  429 maps to `bibliofabric.RateLimitError` in the framework, and the live
  tests skip on it.
- Batch POSTs are reads, sent with `retry=True`; `fields` is a query
  parameter there, not body content; responses are bare arrays with `null`
  placeholders that the clients drop.
- Key-gated fields (`embedding`, `openAccessDoi`, author
  `externalIds`/`papers`) answer HTTP 400 keyless; the client sends them
  and lets the API decide.
- Paper ids travel verbatim (colons and slashes included); never normalize.
- No sessions, no loguru: stdlib logging throughout.

## Development

Commands live at the workspace root (see the root `AGENTS.md`).
Package-specific bits: regenerate sync twins with
`uv run python scripts/unasync.py --package scholiast`, run the
suite with `uv run pytest packages/scholiast/tests`, and run the
live tests with `uv run pytest -m live_api
packages/scholiast/tests` (no credentials needed; the repo
`.env` key answered 403 on 2026-11-27 and is inactive).

## Testing

`tests/_async/` is the source of truth (sync twin generated in
`tests/_sync/`, plus hand-written `tests/test_sync_in_event_loop.py`).
Tests without I/O live directly under `tests/` and run once
(`test_settings.py`). Tests use pytest-httpx: responses are registered
with `add_response(json=...)` without URLs, and the outgoing shape is
asserted through `httpx_mock.get_requests()`. Real payload fixtures live
in `tests/fixtures/`, trimmed from live responses captured on 2026-11-27
(a few envelopes that stayed at 429 all day are built from the published
spec and marked in `docs/upstream-quirks.md`).
`tests/_async/test_live_api.py` (and its `_sync` twin) carries the
`live_api` marker, makes at most one request per second, and skips with
`rate limited` on a 429.

## Known gaps

- The relevance-search route (`/paper/search`) never answered 200 keyless
  during the study; its envelope is implemented from the docs and the
  parent's earlier verification. Live coverage of it will pass once a key
  with access is available.
- `URL:` and `PubMedCentral:` paper ids and the patent search routes were
  not observed with a 200 keyless (429 window); they are implemented per
  the published spec.
- Dataset file downloads are plain HTTP against pre-signed URLs and are
  not wrapped.
