---
hide: true
name: bibliofabric-sibling-client
description: "Procedure for adding a new bibliofabric-family API client package to the utsmok/bibliofabric monorepo (scaffold from the aletheca pattern, dedicated live sweep, tag-driven PyPI trusted publishing)."
---

# Adding a bibliofabric sibling client

The family lives in one monorepo (`utsmok/bibliofabric`, uv workspace). A new
client is a new directory `packages/<name>/`, NOT a new repo. Proven
end-to-end 2026-09-04 with stavrophora (Crossref), alongside aletheca
(OpenAlex) and AIREloom (OpenAIRE). Use when adding a new source client.
The Wave 1 clients built on 2026-11-27 are listed in
`docs/roadmap/wave-1-libraries.md`. `packages/rorifer/` is the closest
template for a client built on the current framework, with the default
headers hook and the identifier normalizers.

## 1. Study, then scaffold

- Read the root `AGENTS.md`, `docs/bibliofabric/authoring-sync.md`, and the closest sibling package completely (`packages/aletheca/` is the canonical shape).
- Create `packages/<name>/` with the family shape: `src/<pkg>/` with `_async/client.py` (`<Name>Client(BaseApiClient)`, resources as `functools.cached_property`), `_async/resources/` (one small module per entity subclassing the dialect-aware base), generated `_sync/` twins (from `uv run python scripts/unasync.py`), pure modules `config.py` (pydantic-settings, `<PKG>_` env prefix, one `@lru_cache get_settings()`), `dialect.py` (`QueryDialect` instances + the resource base subclass with hook overrides), `unwrapper.py`, `filters.py` (pydantic filter models), `models/` (pydantic `extra="allow"`, all fields optional, SafeStr/SafeList coercion), `tests/_async/` (pytest-httpx per-entity + unwrapper tests) + generated `tests/_sync/`, `py.typed`, `LICENSE`, `README.md` (PyPI long description), `CHANGELOG.md` (Keep a Changelog).
- The `packages/*` workspace glob picks the package up automatically. Declare the dependency `bibliofabric>=0.8,<0.9`; uv resolves it to the sibling via the root `[tool.uv.sources]`. No per-package dev groups, ruff/pytest config, `uv.lock`, `.python-version`, `.pre-commit-config.yaml`, or CI workflow — all of that is root-level now.
- Conventional commits, no AI attribution. `LICENSE` (MIT, Samuel Mok) exists once at the repo root if needed.
- Placeholder names: a package can be built before its PyPI name is chosen. Use three spellings with no variation (`tbd_<x>`, `TBD_<X>_`, `Tbd<X>`) and never publish under the placeholder. To rename, replace the PascalCase spelling first, then the upper case prefix, then the lower case name (all case-sensitive, also in `.env`), move the `packages/`, `src/`, and `docs/` directories, then run `uv lock`, `uv run python scripts/unasync.py`, `uv run ruff check --fix`, and `uv run ruff format` (the new names change import sort order). The Wave 1 rename on 2026-11-28 followed these steps.
- Tests: build settings in a test with every credential field explicit (for example `_env_file=None, api_key=None`). `_env_file=None` does not hide variables exported in the shell.
- Packages written in parallel: `uv run` fails while a `packages/*` directory has no `pyproject.toml` yet. Write `pyproject.toml` last. Until then, run the tools from `.venv/bin/` with `PYTHONPATH=packages/<name>/src`, which `ty` needs to resolve the package.

## 2. Extract API semantics LIVE before finalizing models

- 400 validation-failure bodies enumerate the full valid filter list for a route — build filter models from them, not from docs alone.
- Verify with real requests: paging params (some APIs hard-reject unknown params; some ignore rows), cursor/exhaustion semantics, auth/polite-pool mechanism AND its observable proof (e.g. `x-rate-limit-*` header values differ per pool), batch-OR syntax (Crossref: pipe returns 0 results; repeated keys are OR), 404 body shapes (may be text/plain), single-item vs list route schema drift.
- Run one real smoke call per resource before declaring the model set done.
- A fixture from one record is not evidence for a model. Validate the models against a few hundred real records from broad queries (iterate with `on_error="skip"` and count the `failures`) before declaring them done. On 2026-11-28 the Europe PMC client rejected every real record that carried keywords, because its keyword model came from one record without them.
- Wrap every public read route, also when another route returns overlapping data (the POST variant of a search, a record-by-id route, an HTML page the client can parse). Walk the route list of the upstream documentation or OpenAPI document and name next to each route what covers it, before writing the deferred list.

## 3. Gates

- From the repo root: `uv sync --all-packages --all-groups`, `uv run python scripts/unasync.py --check`, `uv run pytest packages/<name>/tests`, `uv run ruff check`, `uv run ruff format --check`, `uv run ty check packages/*/src packages/*/tests scripts/unasync.py` (ty is the family's type checker, no mypy), and `uv run mkdocs build --strict`.
- Known family gotcha: runtime-valid but spec-invalid annotations (e.g. `TTLCache[str, Any]` with non-generic cachetools classes) pass pytest but fail newer ty — fix the annotation, not the pin.

## 4. Dedicated live sweep (owner-required standard, same bar for every client)

- Script a sweep run from the workspace venv; budget requests explicitly and report usage.
- Persist-then-parse: write every raw payload to `/tmp/<pkg>_sweep_artifacts/` IMMEDIATELY on receipt, before any parsing — a report-stage crash must not destroy evidence.
- Cover: every resource's supported ops (get + search/list; assert-by-design where a route intentionally doesn't exist), scoped sub-resources (e.g. `journals.works(issn)`), batch at its size boundary, cursor continuation (N pages, assert no duplicate ids), and raw-vs-parsed field compares (~5 documented fields on each of the richest models, comparing httpx-direct JSON against `model_validate` output). Confirm `extra="allow"` absorbs undocumented keys and coercions behave.
- Triage: client bug → fix in `packages/<name>/` + mocked regression test, commit (family style); API quirk → append to the package README quirks section and/or the docs quirks page. Re-run the mocked suite green after every fix.
- Have a second reviewer run their own probe script — wrong assumptions in the sweep script are the usual false alarm (check get()-returns-model vs envelope semantics and the client's actual kwarg names first).

## 5. Wire-up and release

- Add to the root `mkdocs.yml`: a nav section for the package (move its docs pages to `docs/<name>/`) and its src path to the mkdocstrings `paths`. Add the `tests` path to `testpaths` in the root `pyproject.toml` (without it the root `uv run pytest` silently skips the package). Add a row to the root README table and to `docs/index.md`. Add the package to the test matrix in `.github/workflows/ci.yml`.
- Trusted publishing (once, per package): on pypi.org register a pending project with publisher = `utsmok/bibliofabric` + workflow `ci.yml` + environment `pypi`. The publish job already builds whatever package the tag names.
- Release: bump `version` in `packages/<name>/pyproject.toml`, changelog entry, push main, then `git tag <name>-v0.1.0 && git push origin <name>-v0.1.0` — lint, test matrix, docs, and publish run automatically. Verify with `pypi.org/pypi/<name>/json`.
- Consumers (ut-metadata) add the dependency only after the PyPI release lands; fix client-layer gaps in the package, never as local shims.
