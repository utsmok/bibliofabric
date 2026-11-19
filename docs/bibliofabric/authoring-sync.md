# Writing a client with sync support

This page is the recipe for the three family clients (aireloom, aletheca,
stavrophora) and any new client: move the I/O code into `_async/`, use the
`_concurrency` primitives, add a replacement map entry, and let
`scripts/unasync.py` generate the sync twins.

## 1. File layout

Only modules that do I/O move. Pure modules stay where they are and are
imported by both variants.

```
src/<pkg>/
  client.py            -> src/<pkg>/_async/client.py     # moved (I/O)
  resources/*.py       -> src/<pkg>/_async/resources/…   # moved (I/O)
  _async/_concurrency.py          # hand-written async primitives (already exist in core)
  _sync/                          # GENERATED; do not edit
  config.py, dialect.py, models/, ids.py, ...   # stay put (pure)
  __init__.py                     # exports async and sync names
tests/
  _async/test_client.py           # moved; the source of truth for behavior
  _sync/                          # GENERATED copies
```

## 2. Rules for `_async` sources

Never import `asyncio` in an `_async` module. Use the primitives from the
core's `bibliofabric._async._concurrency` (imported as `from ._concurrency
import ...` inside the package); the generator maps them to their sync twins:

| Write | Async behavior | Generated sync behavior |
|---|---|---|
| `sleep(seconds)` | `asyncio.sleep` | `time.sleep` |
| `Lock` | `asyncio.Lock` | `threading.Lock` |
| `Limiter(rate_limits, max_concurrency)` | per-class gates + shared semaphore | same, thread-safe |
| `run_bounded(fn, items, concurrency)` | semaphore + `gather` | `ThreadPoolExecutor`, order preserved, first error re-raised |
| `maybe_await(value)` | awaits awaitables | returns the value |

Other rewrites the generator applies automatically: `async`/`await` removed,
`AsyncIterator` -> `Iterator`, `__aenter__` -> `__enter__`, `aclose` ->
`close`, `async_authenticate` -> `authenticate`, `httpx.AsyncClient` ->
`httpx.Client`, `AsyncRetrying` -> `Retrying`, and `_async` -> `_sync` in
module paths.

## 3. Naming rule

Every class defined in an `_async` module `X` becomes `SyncX` in the twin,
except classes whose name ends in `Client`: `<Name>Client` becomes
`<Name>SyncClient` (`AlethecaClient` -> `AlethecaSyncClient`,
`WorksClient` -> `WorksSyncClient`, `StavrophoraClient` -> `StavrophoraSyncClient`). The
core framework classes are fixed exceptions: `BaseApiClient` ->
`SyncBaseApiClient`, `ResourceClient` -> `SyncResourceClient`. Private helper
classes (leading underscore) keep their name. You do not configure any of
this; the generator derives it from the class definitions.

## 4. Replacement-map config entry

Add a `[tool.unasync]` table to your package's `pyproject.toml` for token
replacements beyond the standard set (rare; for example a method your client
renames in the sync twin):

```toml
[tool.unasync]
replacements = { "fetch_page" = "fetch_page_sync" }
```

The table merges over the standard replacements for your package only.

## 5. Update the package `__init__.py` and imports

Import both variants from the package root:

```python
from ._async.client import AlethecaClient
from ._async.resources import WorksResource
from ._sync.client import AlethecaSyncClient
from ._sync.resources import SyncWorksResource
```

In-repo code imports the core from the package root (`from bibliofabric import
BaseApiClient`), never `bibliofabric.client`.

## 6. Generate and verify

Run from the repository root:

```bash
uv run python scripts/unasync.py    # writes/refreshes _sync/ and tests/_sync/
uv run ruff format --check && uv run ruff check
uv run pytest packages/<pkg>
uv run python scripts/unasync.py --check   # what CI and pre-commit run
```

Tests live in `tests/_async/` and must not import `asyncio` either; write
concurrency tests with `run_bounded` and the `_concurrency` primitives so the
generated `tests/_sync/` copy runs unchanged. A test that only makes sense for
the sync variant (for example calling the sync client inside a running event
loop) lives in `tests/` outside `_async/` and is not generated.
