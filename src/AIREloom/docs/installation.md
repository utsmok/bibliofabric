# Installation

## Recommended: Using `uv`

The preferred way to install AIREloom is using `uv`, a fast Python package installer and resolver.

*   If `uv` is managing your project's virtual environment, you can add AIREloom as a dependency:
    ```bash
    uv add aireloom
    ```
*   Alternatively, you can install it into the current environment using `uv pip`:
    ```bash
    uv pip install aireloom
    ```

This will install the latest stable version from PyPI.

## Alternative: Using `pip`

You can also install AIREloom using `pip`:

```bash
pip install aireloom
```
This will also install the latest stable version from PyPI.

## From Source (for Development)

If you want to contribute to AIREloom or need the very latest (potentially unreleased) changes, you can install it from a local clone of the repository.

1.  **Clone the repository:**
    If you haven't already, clone the AIREloom repository (or your fork):
    ```bash
    # If you're cloning the main repository:
    git clone https://github.com/utsmok/aireloom.git
    cd aireloom
    # Or if you've forked it:
    # git clone https://github.com/YOUR_USERNAME/aireloom.git
    # cd aireloom
    ```

2.  **Set up the environment and install with `uv`:**
    AIREloom uses `uv` for environment and dependency management.
    ```bash
    uv init  # Initializes a virtual environment if one isn't already active/created
    uv sync --all-extras # Installs AIREloom in editable mode along with all dev, test, and docs dependencies
    ```
    The `uv sync --all-extras` command reads the `pyproject.toml` file and installs the package itself in editable mode (`-e .`) plus all optional dependency groups defined (like `dev`, `test`, `docs`). This means changes you make to the source code will be immediately reflected in your environment.

After these steps, your development environment will be ready. You can run tests using `uvx pytest` and format/lint code using `uvx ruff format .` and `uvx ruff check --fix .`.
