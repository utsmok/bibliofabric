# Contributing to AIREloom

We welcome contributions to AIREloom! Whether you're fixing a bug, adding a new feature, or improving documentation, your help is appreciated.

## How to Contribute

There are several ways you can contribute:

*   **Reporting Bugs:** If you encounter a bug, please file an issue on our [GitHub Issues page](https://github.com/utsmok/aireloom/issues). Include as much detail as possible, such as:
    *   AIREloom version.
    *   Python version.
    *   Steps to reproduce the bug.
    *   Expected behavior.
    *   Actual behavior (including any error messages and stack traces).
*   **Suggesting Enhancements or New Features:** If you have an idea for a new feature or an improvement to an existing one, please open an issue on GitHub to discuss it. This allows us to coordinate efforts and ensure the suggestion aligns with the project's goals.
*   **Improving Documentation:** If you find parts of the documentation unclear, incomplete, or incorrect, please let us know by opening an issue or, even better, submitting a pull request with your improvements.
*   **Writing Code:** If you'd like to contribute code, please follow the development workflow outlined below.

## Development Workflow

### 1. Setting Up Your Environment

This project uses `uv` for managing Python environments and dependencies.

1.  **Fork the Repository:**
    Start by forking the [AIREloom repository](https://github.com/utsmok/aireloom) on GitHub to your own account.

2.  **Clone Your Fork:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/aireloom.git
    cd aireloom
    ```

3.  **Initialize and Sync Environment with `uv`:**
    Ensure you have `uv` installed. Then, set up the virtual environment and install dependencies, including development tools and optional extras:
    ```bash
    uv init
    uv sync --all-extras  # Installs main dependencies + dev, test, docs extras
    ```
    This command reads the `pyproject.toml` file and sets up your environment accordingly.

### 2. Making Changes

1.  **Create a New Branch:**
    Create a new branch for your changes. Choose a descriptive branch name (e.g., `fix/issue-123-timeout-bug` or `feat/add-new-endpoint`).
    ```bash
    git checkout -b your-branch-name
    ```

2.  **Write Your Code:**
    Make your changes, adhering to the coding standards (see below).

### 3. Coding Standards

*   **Formatting and Linting with Ruff:**
    We use [Ruff](https://beta.ruff.rs/docs/) for code formatting and linting. Before committing your changes, please format and lint your code:
    ```bash
    uvx ruff format .
    uvx ruff check --fix .
    ```
    This ensures a consistent code style across the project. Our Ruff configuration is defined in `pyproject.toml`.
*   **Type Hinting:**
    Please use type hints for all function signatures and variables where appropriate. This improves code readability and helps catch errors.
*   **Docstrings:**
    Write clear and concise docstrings for all public modules, classes, functions, and methods. We generally follow the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) for docstrings.

### 4. Running Tests

AIREloom uses `pytest` for testing. Ensure all existing tests pass and add new tests for any new functionality or bug fixes.

*   **Run all tests:**
    ```bash
    uvx pytest
    ```
    Or, if you have activated the virtual environment (`source .venv/bin/activate` or `.\.venv\Scripts\activate`):
    ```bash
    pytest
    ```
*   **Run specific tests:**
    You can run tests for a specific file or test function:
    ```bash
    uvx pytest tests/resources/test_research_products_client.py
    uvx pytest tests/test_session.py::TestAireloomSession::test_session_creation
    ```

### 5. Submitting a Pull Request (PR)

1.  **Commit Your Changes:**
    Make small, logical commits with clear and descriptive commit messages.
    ```bash
    git add .
    git commit -m "feat: Add support for X feature"
    ```

2.  **Push to Your Fork:**
    ```bash
    git push origin your-branch-name
    ```

3.  **Open a Pull Request:**
    Go to your fork on GitHub and open a pull request to the `main` branch of the `utsmok/aireloom` repository.
    *   Provide a clear title and description for your PR.
    *   Reference any related issues (e.g., "Closes #123").
    *   Ensure your PR passes all automated checks (CI).

## Code of Conduct

While we don't have a formal Code of Conduct document yet, we expect all contributors to interact respectfully and constructively.

Thank you for considering contributing to AIREloom!
