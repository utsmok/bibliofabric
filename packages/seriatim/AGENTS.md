# seriatim: Project Guide

seriatim is an async + generated-sync Python client for the ISSN Portal,
built on bibliofabric 0.8. Not yet published.

## Architecture

Async I/O modules under `_async/` are the single source of truth;
`scripts/unasync.py --package seriatim` generates the `_sync/` twins
(`SeriatimSyncClient`, `RecordsSyncClient`, `IssnLSyncClient`, `SearchSyncClient`,
`LtwaSyncClient`):

```
SeriatimClient / SeriatimSyncClient   # _async/client.py -> _sync/client.py
 ├─ records                          # _async/resources.py -> _sync/resources.py (cached_property)
 ├─ issn_l                           # _async/resources.py -> _sync/resources.py (cached_property)
 ├─ search                           # _async/search.py -> _sync/search.py (cached_property)
 └─ ltwa                             # _async/ltwa.py -> _sync/ltwa.py (cached_property)
```

| File(s) | Role |
|---|---|
| `_async/client.py` | `SeriatimClient(BaseApiClient)`. No credentials. `default_headers` sends `Accept: application/ld+json`; the HTML routes answer HTML regardless and their clients parse the body. |
| `_async/resources.py` | `RecordsClient` (`/resource/ISSN/{issn}`) and `IssnLClient` (`/resource/ISSN-L/{issn}`): `get` returns the typed model with `raw` holding the node, `raw` returns the node dict, `exists` uses `GET`. `normalize_id` validates the check digit client-side (`require_issn`), because the Portal answers invalid values with HTTP 400 and the compact spelling with 404. |
| `_async/search.py` | `SearchClient` over `/search`. The Portal answers HTML only, so `page` parses the result page (`data-hits` total, one row per record), `iterate` walks pages (`page`/`page_size` params), `count` reads the total. Repeated form keys (`partner_repositories`, `media`, `category`, `iso_country`) travel as `httpx.QueryParams` pairs because `BaseApiClient.request` types `params` as a mapping. |
| `_async/ltwa.py` | `LtwaClient` over `/ltwa`: one HTML table per request, `page` and `iterate`. The page carries no total, so iteration stops on the first empty page. |
| `dialect.py` | Constants: base URL, JSON-LD route prefixes (`ISSN`, `ISSN-L` only; `ISSN-H` answers HTML), search page sizes (20/30/50/100), sort values, LTWA page size cap (100), and the item-only `QueryDialect`. |
| `filters.py` | `is_valid_issn` (modulo 11 check digit) and `require_issn` (normalize + validate, strips URL forms). |
| `parser.py` | `parse_issn_record` and `parse_issn_l` validate one JSON-LD node via `bibliofabric.validate_model` and store the untouched node on `record.raw`. `record_issn` reads the `#ISSN` node or the `identifier` fallback. |
| `search_parser.py` | `parse_search_page`: stdlib `html.parser` state machine over `search-results__hits-items` (`data-hits`) and `search-results__record` rows (`data-issn`, `data-issnl`, `data-issnh`, `data-cancelled-issn`, `data-medium`, `data-country`, `data-category`, `data-key-title`, "Other Medium" links). Raises `APIError` with a body excerpt when the container is missing. |
| `ltwa_parser.py` | `parse_ltwa_page`: reads `ltwa-results__table-row` rows; an empty abbreviation cell that reads `None` maps to `None`. |
| `unwrapper.py` | `SeriatimUnwrapper`: the JSON-LD node is the item; no envelope, totals, or cursor. |
| `config.py` | `SeriatimSettings(BaseApiSettings)`, env prefix `SERIATIM_`, `.env` support, `get_settings()` cached. Defaults: 1 request per second, concurrency 2. No credential field. |
| `models/` | Pydantic v2 models, `extra="allow"`, `populate_by_name`. Hyphenated JSON keys (`hasCancelledISSN-L`) travel under snake_case aliases. `SeriatimRecord.identified_by` models both shapes: the clustered `#ISSN`/`#ISSN-L`/`#KeyTitle` dict and the flat cancelled node with `cancelledInFavorOf`. |

## Conventions

- Base URL `https://portal.issn.org`. No authentication, no write routes.
- Record routes need the hyphenated ISSN; `require_issn` rejects bad check
  digits before a request leaves the process.
- `format` values read `medium:Print` or `medium:Online`; search rows show
  the codes `ta` (print) and `cr` (online) with their display labels.
- No sessions, no loguru: stdlib logging throughout.

## Development

Commands live at the workspace root (see the root `AGENTS.md`). Package
specifics: regenerate sync twins with `uv run python scripts/unasync.py
--package seriatim`, run the suite with `uv run pytest
packages/seriatim/tests`, and the live tests with
`uv run pytest -m live_api packages/seriatim/tests` (no credentials needed;
about a dozen paced requests).

## Testing

`tests/_async/` is the source of truth (sync twin generated in
`tests/_sync/`, plus hand-written `tests/test_sync_in_event_loop.py`). Tests
without I/O live directly under `tests/` (`test_parsing.py`,
`test_settings.py`) and run once. Fixtures are trimmed real payloads: seven
JSON-LD nodes, the search result markup, and LTWA table markup from
2026-11-27. pytest-httpx responses are registered without URL matchers and
the outgoing shape is asserted through `httpx_mock.get_requests()`.

## Known gaps

- The search rows are a scrape of server-rendered HTML; a Portal redesign
  breaks `SearchClient`, and `parse_search_page` raises `APIError` instead
  of returning guesses.
- The Portal's `/ltwa-export` CSV route answered 502 on 2026-11-27 and is
  not wrapped.
- The SRU Search API and OAI-PMH need a paid subscription; no public
  endpoint exists without credentials.
- `/resource/ISSN-H/` and the ROAD and publishers.issn.org views answer HTML
  only and are not wrapped.
