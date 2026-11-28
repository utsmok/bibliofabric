# Contributing

The `bibliofabric` monorepo hosts the `bibliofabric` core and one client
library per API (`aireloom`, `aletheca`, `stavrophora`, and more) in a single
`uv` workspace under `packages/<name>/`. Requires Python 3.12+ and
[uv](https://docs.astral.sh/uv/).

## Set up your environment

Run everything from the monorepo root:

```bash
git clone https://github.com/YOUR_USERNAME/bibliofabric.git
cd bibliofabric
uv sync --all-packages --all-groups
```

This installs every workspace package in editable mode along with the
`dev` (`pytest`, `pytest-asyncio`, `pytest-httpx`, `ruff`, `ty`, `unasync`)
and `docs` (`mkdocs`, `mkdocs-material`, `mkdocstrings`) dependency groups.

## Async sources and generated `_sync/` twins

For every package, async modules under `packages/<name>/src/<name>/_async/`
and `packages/<name>/tests/_async/` are the single source of truth. Never
hand-edit generated `_sync/` files; regenerate them with `scripts/unasync.py`:

```bash
uv run python scripts/unasync.py                  # regenerate all packages
uv run python scripts/unasync.py --package <name> # regenerate one package
```

See [Writing a client with sync support](bibliofabric/authoring-sync.md) for
the sync-twin rules.

## Quality gates

Every pull request must pass the same gates CI runs:

```bash
uv run python scripts/unasync.py --check
uv run ruff check
uv run ruff format --check
uv run ty check packages/*/src packages/*/tests scripts/unasync.py
uv run pytest
uv run mkdocs build --strict
```

Useful local helpers:

- `uv run ruff check --fix` / `uv run ruff format` — apply lint fixes and formatting.
- `uv run pytest packages/<name>/tests` — run a single package's offline unit suite (`pytest-httpx`).
- `uv run pytest -m live_api` — run live API smoke tests (deselected by default; reads credentials from `.env` files that are git-ignored).
- `uv run mkdocs serve` — preview the documentation site locally.

The `dev` group pins `ty` and `ruff` versions so local checks match CI.

## Conventions

- Use `uv` for all commands (`uv run`, `uv sync`); never bare `python` or `pip`.
- Add type hints on all public signatures; `ty` must pass with zero diagnostics
  and zero suppression comments (`# ty: ignore` / `# type: ignore`).
- Use stdlib `logging` with module loggers (no `loguru`); format debug logs
  with `%s` and redact credentials via `bibliofabric.utils.sanitize_url` and
  `sanitize_headers`.
- Validation failures raise `bibliofabric.ValidationError` with the offending
  payload attached.
- User-facing changes get a Keep a Changelog entry in
  `packages/<name>/CHANGELOG.md`.
- Write small, focused, conventional commits (`feat:`, `fix:`, `docs:`,
  `chore:`, ...), short and imperative, with no AI attribution.

## Wave 1 packages

The eleven Wave 1 packages (`rorifer` through `seriatim`) are finished client
libraries that wait for their first PyPI release. The
[Wave 1 roster](roadmap/wave-1-libraries.md) lists them with their upstream
APIs.

In a test, build settings with every credential field explicit, for example
`OrchisSettings(_env_file=None, access_token=None)`. The `_env_file=None`
argument stops the `.env` file from loading, but it does not hide variables
that the shell exports, so the suite must pass in both situations.

## Submit a pull request

1. Branch from `main`.
2. Push your branch and open a pull request against
   [utsmok/bibliofabric](https://github.com/utsmok/bibliofabric).
3. Reference related issues (e.g. `Closes #123`).
