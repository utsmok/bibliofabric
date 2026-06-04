# Bibliofabric — Project Guide

## What It Is

Bibliofabric is a generic, async Python framework for building scholarly API client libraries. It provides the reusable infrastructure — HTTP client, auth, response parsing, pagination, caching, rate limiting, error handling — so that specific client implementations only need to define the API-specific parts.

[AIREloom](https://github.com/utsmok/aireloom) (an OpenAIRE Graph + Scholix client) is the reference implementation.

**Status:** Alpha. Architecture is settled; needs more client implementations for validation.

## Architecture

```
BaseApiClient              # Generic async HTTP client (client.py)
├── retries (tenacity)
├── caching (TTLCache)
├── rate limiting (header parsing + throttling)
├── pre/post request hooks
└── auth strategy injection
    ├── NoAuth
    ├── StaticTokenAuth
    └── ClientCredentialsAuth (OAuth2)

ResponseUnwrapper          # Protocol — API-specific response parsing (models.py)

BaseResourceClient         # Base for per-endpoint clients (resources.py)
├── GettableMixin           # get(entity_id)
├── SearchableMixin         # search(params) — paginated
├── CursorIterableMixin     # iterate(params) — cursor-based async iterator
└── PageIterableMixin       # iterate(params) — page-based async iterator

BaseApiSettings            # pydantic-settings config (config.py)
```

### Key Layers

| Layer | File | Role |
|-------|------|------|
| **Client** | `client.py` | `BaseApiClient` — generic async HTTP client. ~825 lines. Handles retries, caching, rate limiting, auth, hooks, error mapping. |
| **Auth** | `auth.py` | `AuthStrategy` protocol + 3 implementations: `NoAuth`, `StaticTokenAuth`, `ClientCredentialsAuth`. |
| **Models** | `models.py` | `ResponseUnwrapper` protocol — the key abstraction that makes the framework API-agnostic. |
| **Resources** | `resources.py` | `BaseResourceClient` + 4 composable mixins for REST operations. |
| **Config** | `config.py` | `BaseApiSettings` (pydantic-settings). Subclass with an `env_prefix` per API. |
| **Exceptions** | `exceptions.py` | Hierarchical exceptions: `BibliofabricError` → `APIError`, `TimeoutError`, `NetworkError`, `AuthError`, etc. |
| **Types** | `types.py` | `RequestData` model, `PreRequestHook` / `PostRequestHook` type aliases. |
| **Logging** | `log_config.py` | Loguru-based logging configuration. |

## Tech Stack

- **Python 3.12+**, `uv` for dependency management
- **httpx** — async HTTP
- **tenacity** — retry logic
- **pydantic v2** + **pydantic-settings** — models and config
- **cachetools** — TTL cache
- **loguru** — logging
- **pytest** + **pytest-asyncio** + **pytest-httpx** — testing
- **ruff** — linting/formatting
- **mkdocs-material** + **mkdocstrings** — docs

## Project Structure

```
src/bibliofabric/
  __init__.py           # Package init, version from importlib.metadata
  client.py             # BaseApiClient (~825 lines)
  auth.py               # AuthStrategy protocol + 3 implementations
  models.py             # ResponseUnwrapper protocol
  resources.py          # BaseResourceClient + 4 mixins
  config.py             # BaseApiSettings (pydantic-settings)
  exceptions.py         # Exception hierarchy
  types.py              # RequestData, hook type aliases
  log_config.py         # Loguru configuration
tests/
  test_client.py        # BaseApiClient tests
  test_auth.py          # Auth strategy tests
  test_resources.py     # Mixin and resource client tests
  test_models.py        # ResponseUnwrapper tests
  test_log_config.py    # Logging config tests
docs/                   # MkDocs documentation
```

## Development Commands

```bash
uv sync --all-groups --all-extras    # Install everything
uv run ruff check src/ --fix         # Lint
uv run ruff format src/              # Format
uv run pytest tests/                 # Run tests
uv run pytest --cov=bibliofabric tests/  # Coverage
uv run mkdocs serve                  # Local docs preview
uv run mkdocs build                  # Build docs
```

## Key Patterns & Conventions

- **All I/O is async.** Every method is `async def`. Use `async with` for client lifecycle.
- **Protocol-based extensibility.** `ResponseUnwrapper` and `AuthStrategy` are `Protocol` classes — implement the interface, no inheritance required.
- **Mixin composition.** Resource clients inherit from `BaseResourceClient` + needed mixins (`GettableMixin`, `SearchableMixin`, etc.). Class attributes (`_entity_path`, `_entity_model`) configure behavior.
- **Pydantic settings.** `BaseApiSettings` reads from env vars and `.env` files. Subclass with `env_prefix` per API (e.g., `AIRELOOM_`).
- **No generic `T` type param on `ResponseUnwrapper`.** It works with `dict[str, Any]` — type safety comes from Pydantic models in the consuming library.
- **`extra="allow"`** is the norm for models (forward-compatible with API additions).
- **Error mapping.** `httpx` exceptions are caught and re-raised as the bibliofabric hierarchy inside `BaseApiClient._execute_request`.

## Known Issues & Gaps

- **No published release yet.** Package is installable from git only.
- **Single reference implementation.** AIREloom is the only known consumer. More would validate the abstractions.
- **No streaming support.** All responses are buffered in memory.
- **Cache is in-process only.** `TTLCache` — no shared cache across processes.
- **No request cancellation.** No explicit support for cancelling in-flight requests beyond closing the client.

## Reference Implementation

See [AIREloom](https://github.com/utsmok/aireloom) at `~/dev/AIREloom` for a complete client built on bibliofabric:
- `src/aireloom/client.py` — `AireloomClient(BaseApiClient)`
- `src/aireloom/unwrapper.py` — `OpenAireUnwrapper(ResponseUnwrapper)`
- `src/aireloom/resources/` — Mixin-based resource clients
- `src/aireloom/config.py` — `ApiSettings(BaseApiSettings)` with `env_prefix="AIRELOOM_"`
