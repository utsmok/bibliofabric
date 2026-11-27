# Aletheca — Project Guide

Aletheca is an async + generated-sync Python client for the OpenAlex API, built on bibliofabric 0.6. Published on PyPI as `aletheca`; status alpha.

## Architecture

One generic framework layer (bibliofabric) plus an OpenAlex-specific overlay. Async I/O modules under `_async/` are the single source of truth; `scripts/unasync.py --package aletheca` generates the `_sync/` twins (`AlethecaSyncClient`, `WorksSyncClient`, etc.):

```
AlethecaClient / AlethecaSyncClient   # _async/client.py -> _sync/client.py
 ├─ works/authors/.../locations/links # _async/*.py -> _sync/*.py (cached_property)
 └─ autocomplete(), rate_limit()
```

| File(s) | Role |
|---|---|
| `_async/client.py` | `AlethecaClient(BaseApiClient)`. Resolves credentials (explicit `api_key` > `ALETHECA_API_KEY`/legacy alias env), picks `QueryParameterAuth` (default `?api_key=`) or `StaticTokenAuth` (`auth_scheme="bearer"`), routes `search.semantic` to the 1 req/s `"semantic"` rate class, re-raises keyless 401s with an actionable message, and vetoes retries for 429s with `reason: "daily_budget"` in `is_retryable()`. Adds `autocomplete()` and `rate_limit()` (both wrapped via `bibliofabric.validate_model`). |
| `dialect.py`, `_async/dialect.py` | `OPENALEX_DIALECT` (`per_page`, `iterate_page_size=100`, `cursor`, `sort`, `search`, `select`) and `OpenAlexResourceClient`: single `filter=` serialization with `\|`-joined OR groups (cap 100, `MAX_OR_VALUES`), DOI/ORCID/ROR/ISSN/PMID/PMCID normalization, free `$0` singleton `item_path()` prefixing (`doi:`, `orcid:`, `ror:`, `issn:`, `pmid:`, `pmcid:`), external-ID `record_keys()`, basic-paging 10,000-result cap & `page`+`cursor` guards, `count()` with `select=id`. |
| `_async/{works,authors,...,locations,links}.py` | One client per endpoint (`path`, `model`). `works.py` adds corpus controls, `sample`, `group_by`, `search_scoped`, `citing`/`referenced`, `oa_pdf_urls`, `batch_get_by_doi`, `batch_get_by_openalex_id`. |
| `_sync/*.py` | Generated sync twins from `_async/*.py` via `scripts/unasync.py --package aletheca`; never edit by hand. |
| `filters.py` | Pydantic filter models (including `LocationsFilters` and `LinksFilters`); dot-notation aliases, `extra="allow"`, widened sequence/range types. Deprecated/paid filters deliberately absent. |
| `unwrapper.py` | `OpenAlexUnwrapper`: `meta.count`/`meta.next_cursor`, flattens `meta` into `Page.meta`, keeps envelope extras (e.g. `group_by` buckets). |
| `config.py` | `AlethecaSettings(BaseApiSettings)`, env prefix `ALETHECA_`, `.env` support, `get_settings()` cached. Declares OpenAlex limiter defaults (`max_requests_per_second=10.0`, `max_concurrency=5`, `rate_limits={"semantic": 1.0}`) directly; `api_key` uses `repr=False`. |
| `_helpers.py` | `reconstruct_abstract` (inverted index → text), re-exported from `aletheca`. |
| `models/` | Pydantic v2 entity models, `extra="allow"`, SafeList/SafeStr from bibliofabric. |

## Conventions

- Base URL `https://api.openalex.org`. Auth: `api_key` query param (default) or Bearer.
- Cursor paging: `cursor=*` start, `meta.next_cursor` advance. `per_page` max 100; default 25 for `search()`, 100 for `iterate()`. Basic paging capped at `page * per_page <= 10,000`.
- Filters: `filter=k:v,k2:v2`; list/tuple/set values join with `|` (max 100); `None` and empty collections omitted; booleans lowercase; DOIs normalized.
- No sessions, no loguru: stdlib logging throughout.

## Development

Commands live at the workspace root (see the root `AGENTS.md`). Package-specific bits: regenerate sync twins with `uv run python scripts/unasync.py --package aletheca`, run the suite with `uv run pytest packages/aletheca/tests`, and export `ALETHECA_API_KEY` for `-m live_api`.

## Testing

`tests/_async/` is the source of truth (sync twin generated in `tests/_sync/`, plus hand-written `tests/test_sync_in_event_loop.py`). Tests use pytest-httpx: responses registered with `add_response(json=...)` without URLs (the `api_key` auth param breaks URL matchers); assert outgoing shape via `httpx_mock.get_requests()`. Real payload fixtures live in `tests/fixtures/`. `tests/_async/test_live_api.py` (and `_sync`) carries the `live_api` marker and smoke tests per resource.

## Known gaps

- Filter models cover common filters; `extra="allow"` dicts cover the rest.
