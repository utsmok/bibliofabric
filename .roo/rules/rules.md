# Project Development Guidelines

This document outlines the coding conventions, tools, and best practices for contributing to the `bibliofabric` framework and its associated API client libraries (e.g., `aireloom`). Adhering to these guidelines ensures code quality, consistency, and maintainability across the toolkit.

## 0. Logging and Journalization
- Keep a running journal of changes, to-do's, decisions, issues, etcetera, in
  [`journal.md`](journal.md).
- Follow the plans laid out in [`plan.md`](plan.md), making sure to consult/update the journal in case of changes.The journal is leading in case of conflicts, but can be less robust or detailed.

## 1. Core Principles

-   **Type-Safe:** All new code must include modern type hints (e.g. `list[str | None]`). We aim for 100% type coverage to leverage static analysis for bug prevention.
-   **Async-first:** The libraries are built on `asyncio` and `httpx`. All I/O-bound operations (like API requests) must be asynchronous (`async/await`).
-   **Modular and Decoupled:** We maintain a strict separation between the generic framework (`bibliofabric`) and API-specific implementations. Generic logic should never depend on specific client logic.
-   **Well-Tested:** All features and bug fixes must be accompanied by tests. We aim for high test coverage to ensure reliability.

- Read existing code patterns before implementing new features
- Maintain consistency with existing codebase style
- Provide complete, working code solutions with proper imports
- Include necessary tests and documentation
- Consider performance implications


## 2. Environment and Dependency Management
### 2.1 Package Management

- Use **`uv`** for all Python environment management:
  - `uv run <file>` - Execute Python files in the current environment
  - `uv add <package>` - Add dependencies to the project
  - `uv remove <package>` - Remove dependencies from the project
  - `uv sync` - Synchronize environment with lock file

### 2.2 Code Quality and Formatting
- **`ruff`** for linting and formatting (configured in [`pyproject.toml`](pyproject.toml))
- All code must pass `ruff check .` without warnings before committing
- Use `ruff format .` to auto-format code
- Follow PEP 8 style guidelines with ruff's modern adaptations

### 2.3 Configuration Management
- **[`pyproject.toml`](pyproject.toml)** for project configuration, dependencies, and tool settings
- **`.env`** for secrets and environment variables (never commit to version control)
- Use **`python-dotenv`** to load environment variables into the application
- Store database URLs, API keys, and other sensitive data in `.env`

## 3. Coding Conventions

- **Python 3.13+** is required for all code
- Utilize modern Python features:
  - `match` statements for complex conditional logic
  - Modern type hints: `list[str | None]` instead of `List[Optional[str]]`
  - Union types with `|` syntax: `str | int` instead of `Union[str, int]`
- **Type hints are mandatory** for all function parameters and return types
- **Docstrings are required** for all functions, classes, and modules in Sphinx-compatible format:

```python
def process_data(data: list[dict[str, Any]], validate: bool = True) -> ProcessedData:
    """Process incoming data and return validated results.

    Args:
        data: List of dictionaries containing raw data
        validate: Whether to perform validation checks

    Returns:
        ProcessedData: Validated and processed data object

    Raises:
        ValidationError: If data validation fails
    """
```


## 4. Testing

-   **Framework:** We use `pytest` for writing and running tests.
-   **Asynchronous Tests:** The `pytest-asyncio` plugin is used for testing `async` code.
-   **Running Tests:** To run the entire test suite, use `uv`'s run command:
    ```bash
    uvx pytest
    ```
-   **Test Coverage:** Any new feature or bug fix must include corresponding tests. If you add a new function, add a test for it. If you fix a bug, add a test that would have failed before the fix.
