# Project Development Guidelines

This document outlines the coding conventions, tools, and best practices for contributing to the `bibliofabric` framework and its associated API client libraries (e.g., `aireloom`). Adhering to these guidelines ensures code quality, consistency, and maintainability across the toolkit.

## 1. Core Principles

-   **Type-Safe:** All new code must include modern type hints (e.g. `list[str | None]`). We aim for 100% type coverage to leverage static analysis for bug prevention.
-   **Async-first:** The libraries are built on `asyncio` and `httpx`. All I/O-bound operations (like API requests) must be asynchronous (`async/await`).
-   **Modular and Decoupled:** We maintain a strict separation between the generic framework (`bibliofabric`) and API-specific implementations. Generic logic should never depend on specific client logic.
-   **Well-Tested:** All features and bug fixes must be accompanied by tests. We aim for high test coverage to ensure reliability.


## 2. Environment and Dependency Management

-  This project uses `uv` for environment and dependency management.
-  `uv run script.py` to run python files
-  `uv add <package>` to add a new package to the environment
-  `uv remove <package>` to remove a package from the environment

## 3. Coding Conventions

-   **Formatting & Linting:**
    -   **Tool:** We use [Ruff](https://docs.astral.sh/ruff/) for all formatting and linting.
    -   **Configuration:** The Ruff configuration is defined in `pyproject.toml`. It enforces a line length of 88 characters, `isort` for import sorting, and a strict set of linting rules (including `flake8-bugbear`, `pylint`, `pep8-naming`, etc.).
    -   **Workflow:** Before committing any changes, you must run Ruff to format and fix your code:
        ```bash
        # Format all files
        ruff format .

        # Check for linting errors and apply automatic fixes
        ruff check --fix .
        ```
-   **Type Hinting:**
    -   All function and method signatures must have type hints.
    -   Use modern type hints (e.g., `list[str]` instead of `List[str]`) as the project requires Python 3.12+.
-   **Docstrings:**
    -   All public modules, classes, functions, and methods must have a docstring.
    -   We follow the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) for docstrings. This format is readable and easily parsed by documentation generators.

## 4. Testing

-   **Framework:** We use `pytest` for writing and running tests.
-   **Asynchronous Tests:** The `pytest-asyncio` plugin is used for testing `async` code.
-   **Running Tests:** To run the entire test suite, use `uv`'s run command:
    ```bash
    uvx pytest
    ```
-   **Test Coverage:** Any new feature or bug fix must include corresponding tests. If you add a new function, add a test for it. If you fix a bug, add a test that would have failed before the fix.
