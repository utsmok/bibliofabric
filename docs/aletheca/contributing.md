# Contributing

## Setup

Aletheca lives in the `bibliofabric` uv workspace at `packages/aletheca`. Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/utsmok/bibliofabric.git
cd bibliofabric
uv sync --all-packages --all-groups
```

This installs all workspace packages in editable mode with the `dev` group (pytest, pytest-asyncio, pytest-httpx, ruff, ty, unasync) and the `docs` group (mkdocs, mkdocs-material, mkdocstrings).

## Sync twins

Async modules under `packages/aletheca/src/aletheca/_async/` and `packages/aletheca/tests/_async/` are the source of truth. After editing any `_async/` file, regenerate the `_sync/` twins:

```bash
uv run python scripts/unasync.py --package aletheca
```

## Tests

```bash
uv run pytest packages/aletheca/tests              # unit tests, fast and offline
uv run pytest packages/aletheca/tests -m live_api  # live OpenAlex smoke tests; needs ALETHECA_API_KEY
```

The unit suite uses pytest-httpx and never touches the network. Tests marked `live_api` are deselected by default (`asyncio_mode = "auto"`, so async tests need no markers).

## Lint, types, format

```bash
uv run ruff check --fix packages/aletheca
uv run ruff format packages/aletheca
uv run ty check packages/aletheca/src
uv run python scripts/unasync.py --check
```

## Docs

```bash
uv run mkdocs serve        # local preview
uv run mkdocs build --strict
```

The API reference pages are generated from the source with mkdocstrings; docstrings are user-facing text.

## Releases

Keep a Changelog format in `packages/aletheca/CHANGELOG.md`. Tag `aletheca-v<version>` on `main` to publish via CI.
