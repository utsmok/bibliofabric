# Contributing to Bibliofabric

We welcome contributions! Whether you're fixing a bug, adding a feature, or improving documentation, your help is appreciated.

## How to Contribute

- **Reporting Bugs:** File an issue on [GitHub Issues](https://github.com/utsmok/bibliofabric/issues) with the bibliofabric version, Python version, steps to reproduce, and expected vs. actual behavior.
- **Suggesting Features:** Open an issue to discuss before implementing. This helps coordinate efforts and ensures alignment with the project's goals.
- **Improving Documentation:** Docs live in `docs/` (MkDocs). Fixes and clarifications are always welcome.
- **Writing Code:** Follow the development workflow below.

## Development Workflow

### 1. Set Up Your Environment

This project uses `uv` for dependency management.

```bash
git clone https://github.com/YOUR_USERNAME/bibliofabric.git
cd bibliofabric
uv sync --all-groups --all-extras
```

### 2. Make Changes

Create a descriptive branch:

```bash
git checkout -b fix/issue-123-timeout-bug
```

### 3. Coding Standards

- **Formatting & Linting:** We use [Ruff](https://docs.astral.sh/ruff/).

```bash
uv run ruff format src/
uv run ruff check src/ --fix
```

- **Type Hints:** Use type hints on all public signatures.
- **Docstrings:** Follow the Google Python Style Guide. Every public module, class, and function should have a docstring.

### 4. Running Tests

```bash
uv run pytest tests/                 # All tests
uv run pytest tests/test_client.py   # Specific file
uv run pytest --cov=bibliofabric tests/  # With coverage
```

### 5. Submit a Pull Request

1. Make small, focused commits with clear messages.
2. Push to your fork and open a PR against `main` on `utsmok/bibliofabric`.
3. Reference any related issues (e.g., "Closes #123").

## Code of Conduct

We expect all contributors to interact respectfully and constructively.

Thank you for contributing to bibliofabric!
