# Contributing to Bibliofabric

## Set up your environment

This project uses `uv`:

```bash
git clone https://github.com/YOUR_USERNAME/bibliofabric.git
cd bibliofabric
uv sync --all-groups
```

## Gates

Every change must pass the same gates CI runs:

```bash
uv run ruff check            # lint src and tests
uv run ruff format --check   # formatting
uv run ty check src          # types, zero diagnostics
uv run pytest                # tests
```

`uv run ruff format` to format; `uv run ruff check --fix` for lint fixes. The
`dev` group pins `ty` exactly so local and CI runs agree.

## Conventions

- Type hints on all public signatures; no `# type: ignore` in `src`.
- Standard `logging` with module loggers; debug messages use `%s` formatting
  and redact credentials (`bibliofabric.utils.sanitize_url`,
  `sanitize_headers`).
- Changes that affect consumers get a `CHANGELOG.md` entry.
- Small, focused commits with conventional-commit messages, no AI attribution.

## Submit a pull request

1. Branch from `main`.
2. Push and open a PR against `utsmok/bibliofabric`.
3. Reference related issues, e.g. "Closes #123".
