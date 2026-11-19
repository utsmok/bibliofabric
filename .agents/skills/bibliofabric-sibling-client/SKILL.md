---
hide: true
name: bibliofabric-sibling-client
description: "Procedure for creating, live-verifying, and releasing a new bibliofabric-family API client repo (scaffold from the aletheca pattern, dedicated live sweep, CI + tag-driven PyPI trusted publishing) in the utsmok ecosystem."
---

# Building a bibliofabric sibling client

Procedure proven end-to-end 2026-09-04 with stavrophora (Crossref), alongside aletheca (OpenAlex) and AIREloom (OpenAIRE). Use when adding a new source client to github.com/utsmok (e.g. DataCite, Semantic Scholar, Europe PMC).

## 1. Study, then scaffold

- Read `/home/sam/dev/ut-metadata/docs/research/bibliofabric-family.md` ("Patterns to copy verbatim") and `/home/sam/dev/ut-metadata/docs/research/apis.md` (source facts). Study the closest sibling repo completely (aletheca is the canonical shape).
- Repo skeleton (Python >=3.12, pin `bibliofabric>=0.6,<0.7`, plus `[tool.uv.sources] bibliofabric = { git = "https://github.com/utsmok/bibliofabric", branch = "overhaul-2026-11" }` until bibliofabric 0.6.0 is on PyPI): `src/<pkg>/` with `client.py` (`<Name>Client(BaseApiClient)`, resources as `functools.cached_property`), `config.py` (pydantic-settings, `<PKG>_` env prefix, one `@lru_cache get_settings()`), `dialect.py` (`QueryDialect` instances + the resource base subclass with hook overrides), `unwrapper.py`, `filters.py` (pydantic filter models), `models/` (pydantic `extra="allow"`, all fields optional, SafeStr/SafeList coercion), `resources/` (one small module per entity subclassing the dialect-aware base), tests (pytest-httpx per-entity + unwrapper + batch; live tests marker-gated off via `addopts = "-m 'not live_api'"`).
- Furniture: README in family voice (incl. a "Known <API> Quirks" section), minimal mkdocs.yml + docs/index.md, `.pre-commit-config.yaml` copied from bibliofabric, MIT LICENSE (Samuel Mok), `.gitignore`, `.python-version`, `py.typed`, CI workflow mirroring aletheca's, committed uv.lock. Conventional commits, no AI attribution.

## 2. Extract API semantics LIVE before finalizing models

- 400 validation-failure bodies enumerate the full valid filter list for a route — build filter models from them, not from docs alone.
- Verify with real requests: paging params (some APIs hard-reject unknown params; some ignore rows), cursor/exhaustion semantics, auth/polite-pool mechanism AND its observable proof (e.g. `x-rate-limit-*` header values differ per pool), batch-OR syntax (Crossref: pipe returns 0 results; repeated keys are OR), 404 body shapes (may be text/plain), single-item vs list route schema drift.
- Run one real smoke call per resource before declaring the model set done.

## 3. Gates

- Local: `uv sync --all-groups`, `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uvx ty check src/` (ty is the family's type checker, no mypy).
- If CI enforces `--cov-fail-under`, measure locally BEFORE the first push so a brand-new public repo doesn't debut red.
- Known family gotcha: runtime-valid but spec-invalid annotations (e.g. `TTLCache[str, Any]` with non-generic cachetools classes) pass pytest but fail newer ty — fix the annotation, not the pin.

## 4. Dedicated live sweep (owner-required standard, same bar for every client)

- Script a sweep run from the repo venv; budget requests explicitly and report usage.
- Persist-then-parse: write every raw payload to `/tmp/<pkg>_sweep_artifacts/` IMMEDIATELY on receipt, before any parsing — a report-stage crash must not destroy evidence.
- Cover: every resource's supported ops (get + search/list; assert-by-design where a route intentionally doesn't exist), scoped sub-resources (e.g. `journals.works(issn)`), batch at its size boundary, cursor continuation (N pages, assert no duplicate ids), and raw-vs-parsed field compares (~5 documented fields on each of the richest models, comparing httpx-direct JSON against `model_validate` output). Confirm `extra="allow"` absorbs undocumented keys and coercions behave.
- Triage: client bug → fix in the client's own repo + mocked regression test, commit (family style); API quirk → append to the README quirks section. Re-run the mocked suite green after every fix.
- Have a second reviewer run their own probe script — wrong assumptions in the sweep script are the usual false alarm (check get()-returns-model vs envelope semantics and the client's actual kwarg names first).

## 5. GitHub + release

- `gh repo create utsmok/<name> --public --description ... --source . --push`; add topics; after the first CI run, enable Pages from the `gh-pages` branch (gh-deploy does NOT enable it): `gh api -X POST repos/utsmok/<name>/pages -f source='{"branch":"gh-pages","path":"/"}'`. Watch the first CI run (coverage gate + gh-deploy debut on a new repo) with `gh run watch <id> --exit-status`.
- Trusted publishing (once, per package): on pypi.org register a pending project with publisher = repo + workflow filename + environment Any; then add a `publish` job to the CI workflow: `needs: test`, `if: startsWith(github.ref, 'refs/tags/')`, `permissions: { id-token: write }`, `uv build` + `pypa/gh-action-pypi-publish@release/v1`.
- Release flow thereafter: bump `version` in pyproject, `git tag vX.Y.Z && git push origin vX.Y.Z` — test matrix, docs deploy, and publish run automatically. Verify with `pypi.org/pypi/<name>/json`.
- Consumers (ut-metadata) add the dependency only after the PyPI release lands; fix client-layer gaps in the client repos, never as local shims.
