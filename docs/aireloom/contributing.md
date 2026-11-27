# Contributing to AIREloom

AIREloom lives in the [bibliofabric monorepo](https://github.com/utsmok/bibliofabric)
under `packages/aireloom` (docs under `docs/aireloom`).

## Setup

```bash
git clone https://github.com/utsmok/bibliofabric.git
cd bibliofabric
uv sync --all-packages --all-groups
```

## Making changes

All I/O modules live under `packages/aireloom/src/aireloom/_async/` and their
tests under `packages/aireloom/tests/_async/`. Never edit `_sync/` files by
hand; regenerate them with `scripts/unasync.py`:

```bash
uv run python scripts/unasync.py --package aireloom
```

## Checks

Run the workspace gates from the repository root before opening a pull request:

```bash
uv run pytest packages/aireloom/tests
uv run ruff check packages/aireloom
uv run ruff format --check packages/aireloom
uv run ty check packages/aireloom/src
uv run python scripts/unasync.py --check
uv run mkdocs build --strict
```

To run the live API smoke tests (deselected by default):

```bash
uv run pytest -m live_api packages/aireloom/tests
```

## Conventions

- Use `uv` for all commands.
- Use conventional commit messages (`feat:`, `fix:`, `docs:`, `chore:`).
- Validation failures raise `bibliofabric.ValidationError`; `ty` must pass with
  zero diagnostics and zero ignore comments.
- Report bugs and feature requests on the
  [bibliofabric issue tracker](https://github.com/utsmok/bibliofabric/issues).
