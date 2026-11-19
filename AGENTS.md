# Bibliofabric — Project Guide

## What It Is

Bibliofabric is the shared core of a family of scholarly API client libraries
([AIREloom](https://github.com/utsmok/aireloom) for OpenAIRE,
[aletheca](https://github.com/utsmok/aletheca) for OpenAlex,
[stavrophora](https://github.com/utsmok/stavrophora) for Crossref). It owns
HTTP, auth, retries, throttling, error mapping, paging, batch retrieval,
identifier normalization, and typed resource clients. Each client library adds
only what is specific to its API.

## Architecture

```
BaseApiClient            # async HTTP: retries, throttling, error mapping (client.py)
├── auth strategy        # NoAuth, StaticTokenAuth, QueryParameterAuth,
│                        # HeaderAuth, ClientCredentialsAuth (auth.py)
├── limiter              # max_requests_per_second + max_concurrency
└── retry policy         # is_retryable() veto, Retry-After-aware wait

QueryDialect             # frozen paging/sort/search/select declaration (paging.py)
ResourceClient[E]        # generic typed endpoint client (resources.py)
Page[E]                  # uniform search envelope (paging.py)
ResponseUnwrapper        # protocol for API envelopes (unwrap.py)
BaseApiSettings          # pydantic-settings config (config.py)
```

## Module map

| Module | Contents |
|---|---|
| `client.py` | `BaseApiClient`: `request()` returns `httpx.Response`, raises typed errors; `is_retryable()` veto; `Retry-After`-aware retries; limiter |
| `auth.py` | `AuthStrategy` protocol + `NoAuth`, `StaticTokenAuth`, `QueryParameterAuth`, `HeaderAuth`, `ClientCredentialsAuth` |
| `config.py` | `BaseApiSettings` (timeout, retries, retry wait, limiter knobs, UA, mailto) |
| `exceptions.py` | `BibliofabricError` hierarchy; `APIError.body` carries the parsed JSON error payload; `ValidationError` carries `raw`/`error`/`model_name` |
| `paging.py` | `QueryDialect` (frozen), `Page[E]` |
| `resources.py` | `ResourceClient[E]`: get/search/iterate/collect/first/count/batch_get + hooks (`build_filter_params`, `format_sort`, `build_batch_params`, `normalize_id`, `item_path`) |
| `unwrap.py` | `ResponseUnwrapper` protocol: results/item/total/next_cursor/meta |
| `ids.py` | `normalize_doi`, `is_doi`, `normalize_orcid`, `normalize_ror`, `normalize_issn`, `strip_url_prefix` |
| `types.py` | `SafeStr`, `SafeList` annotated pydantic types |
| `utils.py` | Internal log redaction: `sanitize_url`, `sanitize_headers` |

## Tech Stack

- Python 3.12+, `uv`-managed, `uv_build` backend, `py.typed` shipped
- httpx, pydantic v2 + pydantic-settings, tenacity
- stdlib `logging` (no loguru; no handlers configured by the library)
- dev group: pytest, pytest-asyncio, pytest-httpx, ruff (pinned), ty (pinned exactly)
- docs group: mkdocs-material + mkdocstrings

## Development Commands

```bash
uv sync --all-groups     # install everything
uv run ruff check        # lint src and tests (tests/_legacy excluded)
uv run ruff format --check
uv run ty check src      # zero diagnostics, no ignores
uv run pytest            # tests/ (legacy suite in tests/_legacy is not collected)
uv run mkdocs serve      # local docs preview
```

## Key patterns

- Async only. Clients are async context managers; caller-owned `http_client`s
  are not closed by `aclose()`.
- Errors by default: no raw fallbacks. Validation failures raise
  `ValidationError` with the payload attached; harvesting tolerates bad records
  via `iterate(on_error="skip", failures=[...])`.
- Behavior is declared in frozen dataclasses (`QueryDialect`), not mutable
  class attributes. Per-API variation lives in `ResourceClient` hook methods.
- `batch_get(ids, field="id", batch_size=None, concurrency=4)` chunks,
  normalizes, deduplicates, and keys by normalized id.
- Debug logs redact `api_key`, tokens, and auth headers
  (`sanitize_url` / `sanitize_headers`).

## Status

0.6.0 is the overhaul release. Legacy code and tests are quarantined:
`tests/_legacy/` holds the pre-overhaul suite, excluded from collection and
from ruff; it is deleted in Phase 2.
