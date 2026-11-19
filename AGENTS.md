# AGENTS.md

Guidelines for AI agents and contributors working in the bibliofabric
monorepo.

## Rules

- Use `uv` for everything (`uv run`, `uv sync`); never bare `python` or `pip`.
- Conventional commits (`feat:`, `fix:`, `docs:`, `chore:`, ...), short and
  imperative. No AI attribution in commits.
- Never print or commit secrets; live-test credentials come from `.env`
  files that are git-ignored.
- All four packages are async-only; stdlib `logging` only (no loguru).
- Errors raise; there are no raw-dict fallbacks. Validation failures raise
  `bibliofabric.ValidationError` with the payload attached.
- `ty` gate is zero diagnostics and zero ignore comments. Fix findings by
  declaring attributes properly; never suppress.

## Layout

| Path | Contents |
|---|---|
| `packages/bibliofabric` | core framework (`src/bibliofabric`) |
| `packages/aireloom` | OpenAIRE client |
| `packages/aletheca` | OpenAlex client |
| `packages/stavrophora` | Crossref client |
| `docs/<name>/` | that package's docs pages, one mkdocs site at the root |
| `archive/<name>/` | historical documents from the standalone repos |
| `.agents/skills/` | agent procedures (release, sibling client, live sweep) |

Each `packages/<name>/AGENTS.md` records package-specific facts (architecture,
upstream quirks, testing patterns). Tooling lives only at the root:

- one virtual workspace root `pyproject.toml` (workspace members, `[tool.uv.sources]`
  `bibliofabric = { workspace = true }`, shared `dev` and `docs` groups, ruff and
  pytest config; `ty` needs no config),
- one root `uv.lock`, one root `.python-version` (3.12),
- one CI workflow (`.github/workflows/ci.yml`), one `.pre-commit-config.yaml`,
- one mkdocs site (`mkdocs.yml`, mkdocstrings paths into all four `src` trees).

## Commands

Run everything from the repository root:

```bash
uv sync --all-packages --all-groups   # install all packages plus dev/docs groups
uv run pytest                         # all four suites (46+48+66+83 tests)
uv run pytest packages/aletheca/tests # one package's suite
uv run pytest -m live_api             # live API smoke tests (needs credentials in .env)
uv run ruff check                     # lint all packages
uv run ruff format --check            # formatting gate
uv run ty check packages/*/src        # type gate
uv run mkdocs build --strict          # docs gate
uv build --package <name>             # build one package (wheel contains py.typed)
```

Client packages depend on `bibliofabric>=0.6,<0.7`; inside the workspace uv
resolves that to the sibling package (`[tool.uv.sources]` at the root).

## Release flow

1. Bump `version` in `packages/<name>/pyproject.toml` and add a Keep a
   Changelog entry to that package's `CHANGELOG.md`. Commit and push `main`.
2. Tag `<name>-v<version>` (example: `aletheca-v0.4.1`) and push the tag.
   A plain `v<version>` tag still publishes bibliofabric.
3. CI runs lint + the test matrix, then a publish job that runs
   `uv build --package <name>` and uploads via OIDC to the `pypi`
   environment. One site deploys docs on pushes to `main`.
4. Verify the release is on PyPI before advertising it; `uv`'s index cache
   can lag a fresh publish for minutes (`uv cache clean <pkg>` if `uv add`
   claims the new version is unavailable).

Per-package release notes go in that package's changelog only; the root
README table lists versions and needs a row update only when a package is
added or renamed.

## Adding a package

Create `packages/<new-name>/` with the family shape (`src/<new_name>/` with
`client.py`, `config.py`, `dialect.py`, `unwrapper.py`, `filters.py`,
`models/`, `resources/`; `tests/` with pytest-httpx; `py.typed`; README and
CHANGELOG). The `packages/*` workspace glob picks it up automatically; add a
docs section to the root `mkdocs.yml` nav, a row to the README table, a
matrix entry in `ci.yml`, and a PyPI trusted publisher entry for the new
package name. See `.agents/skills/bibliofabric-sibling-client/` for the full
procedure.
