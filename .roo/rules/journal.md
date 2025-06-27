# Bibliofabric dev journal

*This file serves as a log / journal for developers. All changes, decisions, issues, and to-do's should be recorded here.*
*If it can be avoided, do not delete info from this file, but mark as done/resolved/obsolete/replace/... in order to keep a history of changes and thoughts.*
*Before making any changes or implementing anything, consult this journal, and make sure to add the planned changes to the journal and/or integrate them into the existing notes.*


# Project To-Do List: `bibliofabric` Refactor

*Keep track of all tasks here. Use checkboxes to mark tasks as done.*
*Use indentation to show hierarchy inside lists (tasks/subtasks/...) if needed.*
*Feel free to add new tasks/subtasks/... as needed, always try to keep the structure consistent.*

-   [x] **Phase 0: Establish Project Foundation**
    -   [x] **Task 0.1: Set up new directory structure dependencies etc**
        -   [x] folder src/ should contain the `bibliofabric` folder for the generic package -- initially empty
        -   [x] folder src/ should contain the `aireloom` repo as a submodule
        -   [x] both should have their own `pyproject.toml` files
        -   [x] `aireloom` should have a dependency on the local `bibliofabric` package (to be built): this is the first step in initializing the refactoring process

-   [x] **Phase 1: Develop `bibliofabric` Generic Framework**
    -   [x] **Task 1.1: Migrate Core Modules**
        -   [x] Move `exceptions.py`.
        -   [x] Move `log_config.py`.
        -   [x] Move `types.py`.
        -   [x] Move `auth.py`.
        -   [x] Update all internal imports within these files.
    -   [x] **Task 1.2: Create Generic Settings**
        -   [x] Create `bibliofabric/config.py`.
        -   [x] Define `BaseApiSettings` with only generic fields (timeout, retries, cache, etc.).
    -   [x] **Task 1.3: Define Core Protocols**
        -   [x] Create `bibliofabric/models.py`.
        -   [x] Define the `ResponseUnwrapper` protocol inside it.
    -   [x] **Task 1.4: Implement the `BaseApiClient`**
            -   [x] Create `bibliofabric/client.py`.
            -   [x] Implement `BaseApiClient`, ensuring its `__init__` accepts a `ResponseUnwrapper`.
            -   [x] Port all generic request, retry, cache, and rate-limit logic from `aireloom`.
    -   [x] **Task 1.5: Implement Generic Resource Mixins**
        -   [x] Create `bibliofabric/resources.py`.
        -   [x] Implement `BaseResourceClient`.
        -   [x] Implement `GettableMixin`.
        -   [x] Implement `SearchableMixin`.
        -   [x] Implement `CursorIterableMixin`.

-   [x] **Phase 2: Refactor `aireloom` to use `bibliofabric`**
    -   [x] **Task 2.1: Implement the OpenAIRE Unwrapper**
        -   [x] Create `aireloom/unwrapper.py`.
        -   [x] Implement `OpenAireUnwrapper` class, satisfying the `ResponseUnwrapper` protocol.
    -   [x] **Task 2.2: Refactor `aireloom` Client & Config**
        -   [x] Update `aireloom.config.ApiSettings` to inherit from `BaseApiSettings`.
        -   [x] Update `aireloom.client.AireloomClient` to inherit from `BaseApiClient`.
        -   [x] Update `AireloomClient.__init__` to pass the `OpenAireUnwrapper` to the parent class.
    -   [x] **Task 2.3: Refactor `aireloom` Resource Clients**
        -   [x] Update `ResearchProductsClient` to use mixins.
        -   [x] Update `ProjectsClient` to use mixins.
        -   [x] Update `OrganizationsClient` to use mixins.
        -   [x] Update `DataSourcesClient` to use mixins.
        -   [x] Verify `ScholixClient` and adapt as needed, keeping its custom logic.

-   [x] **Phase 3: Validate the Refactor**
    -   [x] **Task 3.1: Execute All Tests**
        -   [x] Run `pytest` suite.
        -   [x] Run `verification_script.py`.
    -   [x] **Task 3.2: Resolve All Failures**
        -   [x] Debug any failing tests.
        -   [x] Ensure functionality is identical to the pre-refactor version.
    -   [x] **Task 3.3: Create a real-world example test script for the `aireloom` library**
        -   [X] Create a new test script in the `aireloom` test suite named `test_actual_data.py` or similar.
        -   [X] Follow the `aireloom` guidelines for setting up the client & retrieving data: use the README.md as primary entry point; and the rest of the docs (`src/aireloom/docs`) as reference if needed.
        -   [X] Also set up a manual API retrieval function that calls the OpenAIRE API directly using `httpx` with the  same parameters as the `aireloom` client calls.
    -   [x] **Task 3.4: Use this test to validate the research product endpoint of the `aireloom` library**
          -   [X] Set up a `ResearchProductsFilters` instance to use as a filter for the research_products endpoint. Use the specific parameters listed below.
              -   [X] `authorOrcid`: "0000-0003-0581-2668"
              -   [X] `fromPublicationDate`: "2020-01-01"
          -   [X] Retrieve the list of research products using the filter. Verify that all retrieved items have the expected author listed (i.e. the one with the ORCID "0000-0003-0581-2668", name should be Han Gardeniers or a variant of that).
          -   [X] Solve issues that arise during the process.
                - [X] The parsed output from the `aireloom` client should match the raw output retrieved using `httpx`.
     -   [x] **Task 3.5: Validate all other endpoints using the retrieved research products as a starting point**
          -   [X] Test all other available endpoints (listed below).  Make sure to retrieve more than 1 item from each endpoint.
              -   [X] Projects
                -   [X] Filtered query succesfully run with expected results.
                -   [X] Compare all raw output retrieved using HTTPX with the parsed & verified output from the `aireloom` client (i.e. the pydantic models representing the data).
              -   [X] Organizations
                -   [X] Filtered query succesfully run with expected results.
                -   [X] Compare all raw output retrieved using HTTPX with the parsed & verified output from the `aireloom` client (i.e. the pydantic models representing the data).
              -   [X] Data Sources
                -   [X] Filtered query succesfully run with expected results.
                -   [X] Compare all raw output retrieved using HTTPX with the parsed & verified output from the `aireloom` client (i.e. the pydantic models representing the data).
              -   [X] Scholix
                -   [X] Filtered query succesfully run with expected results.
                -   [X] Compare all raw output retrieved using HTTPX with the parsed & verified output from the `aireloom` client (i.e. the pydantic models representing the data).
      -   [ ] **Task 3.6: Final touches**
          -   [x] Verify that the test suite covers all functionality and edge cases of the `aireloom` client. Basic pytest cmd: `uv run pytest /src/aireloom/tests`. Make sure the coverage is up to spec. (Achieved 91%)
          -   [x] Verify that the test suite covers all functionality and edge cases of the `bibliofabric` package. Basic pytest cmd: `uv run pytest /src/bibliofabric/tests`. Make sure the coverage is up to spec. (Achieved 83%)
          -   [c]  Ensure that all code is properly documented, including: (c = currently in progress)
              -   [x] Docstrings for all classes, methods, and functions in `bibliofabric`.
              -   [c] Docstrings for all classes, methods, and functions in `aireloom`. (Partially done for client.py, config.py, constants.py, endpoints.py)
              -   [ ] Inline comments where necessary to explain complex logic.
          -   [ ] Update all README.md files for both `bibliofabric` and `aireloom` to reflect the new structure and usage.
          -   [ ] Build the documentation for `aireloom` using mkdocs.
          -   [ ] Set up the documentation for `bibliofabric` using mkdocs.
          -   [ ] Build the documentation for `bibliofabric` using mkdocs.
          -   [ ] Ensure that the `aireloom` and `bibliofabric` packages are properly versioned and ready for release, including
              -   [ ] Updating the version number in `pyproject.toml`.
              -   [ ] Ensuring all dependencies are correctly listed and cleaned up.
              -   [ ] Verifying that the package can be installed from source and works as expected.
              -   [ ] Create a release branch for `bibliofabric` and `aireloom` to prepare for the final release.
              -   [ ] Any other final touches that are needed to ensure a smooth release process.



# Decisions & Notes

*Record decisions made during development, including why certain approaches were chosen, alternatives considered, and any relevant context.*
*Keep it concise an clear*
*Any notes for future developers should be added here, including any known issues, limitations, or areas for improvement.*
*Remember to date your entries for future reference.*

## 2025-06-25: Phase 3 - Validation Completed

**What was done:**
- After fixing all import errors and other issues arising from the refactor, the full test suite was executed.
- All `pytest` tests now pass successfully.
- The `verification_script.py` also runs without errors, confirming that the refactored `aireloom` client produces the same output as the original version.

**Conclusion:**
The refactoring is complete and validated. The `bibliofabric` framework successfully abstracts the generic client logic, and the `aireloom` client correctly utilizes it without any loss of functionality. The project is now in a stable state.

**Next steps:**
The main refactoring work is complete. Future work can focus on adding new features, creating clients for other APIs (like Crossref or OpenAlex), or improving documentation.

## 2025-06-25: Phase 0 Configuration Completed

**What was done:**
- Updated root [`pyproject.toml`](../../pyproject.toml) with complete bibliofabric package configuration
  - Added proper project metadata (name, version, description, author)
  - Added all required dependencies: httpx, tenacity, pydantic, pydantic-settings, loguru, cachetools, python-dotenv
  - Configured build system with hatchling and proper package discovery
  - Added development dependencies for testing and linting
  - Configured ruff for code formatting and linting
- Updated [`src/aireloom/pyproject.toml`](../../src/aireloom/pyproject.toml) to include local dependency on bibliofabric using `"bibliofabric @ {root:uri}/../bibliofabric"` syntax
- Created minimal [`src/bibliofabric/__init__.py`](../../src/bibliofabric/__init__.py) with package documentation and version info

**Key decisions:**
- Used Python 3.13+ requirement for both packages to leverage modern type hints and language features
- Added comprehensive ruff configuration for consistent code quality across both packages
- Used local editable dependency syntax for aireloom -> bibliofabric link to enable development workflow

**Next steps:**
Ready to proceed with Phase 1 - implementing the core bibliofabric framework modules.

## 2025-06-25: Phase 1, Task 1.2 - Generic Settings Completed

**What was done:**
- Created [`src/bibliofabric/config.py`](../../src/bibliofabric/config.py) by adapting the aireloom configuration
- Renamed `ApiSettings` to `BaseApiSettings` to reflect its generic nature
- Removed all OpenAIRE-specific fields:
  - `openaire_api_token`, `openaire_client_id`, `openaire_client_secret`, `openaire_token_url`
- Kept all generic API client configuration fields:
  - Request timeout, max retries, backoff factor, user agent
  - Rate limiting settings (enable flag, buffer percentage, retry after default)
  - Caching settings (enable flag, TTL, max size)
  - Pre/post request hooks
- Updated imports to use relative imports from bibliofabric modules (`.types`)
- Updated docstrings to be generic rather than OpenAIRE-specific
- Created `get_base_settings()` function for cached access to base settings
- Used modern Python 3.13+ type hints throughout

**Key decisions:**
- Removed the `env_prefix` default to allow inheriting classes to set their own prefixes
- Changed default user agent to `"bibliofabric/1.0.0"` for generic branding
- Maintained the same configuration structure to ensure easy migration from aireloom
- Kept `arbitrary_types_allowed=True` to support callable hooks

**Next steps:**
Ready to proceed with Task 1.3 - Define Core Protocols (ResponseUnwrapper).

## 2025-06-25: Phase 1, Task 1.3 - Core Protocols Completed

**What was done:**
- Created [`src/bibliofabric/models.py`](../../src/bibliofabric/models.py) with the `ResponseUnwrapper` protocol definition
- Defined the complete `ResponseUnwrapper` protocol interface with four required methods:
  - `unwrap_results(response_json)` - Extract list of result items from API response
  - `unwrap_single_item(response_json)` - Extract single item from API response
  - `get_next_page_token(response_json)` - Extract pagination token for next page
  - `get_total_results(response_json)` - Extract total count of results if available
- Added comprehensive docstrings with detailed examples for OpenAIRE and Crossref API patterns
- Used modern Python 3.13+ type hints throughout (`dict[str, Any]`, `list[dict[str, Any]]`, `str | None`, `int | None`)
- Updated [`src/bibliofabric/__init__.py`](../../src/bibliofabric/__init__.py) to include models module in public API
- Followed project coding conventions with proper Sphinx-compatible documentation

**Key decisions:**
- Used `typing.Protocol` to define the interface, enabling structural subtyping for maximum flexibility
- Designed methods to be generic enough to support various API pagination schemes (cursor-based, offset-based, page-based, link-based)
- Made `get_total_results()` return `int | None` since not all APIs provide total counts
- Made `get_next_page_token()` return `str | None` to handle both pagination tokens and end-of-results cases
- Included comprehensive examples in docstrings showing how different APIs (OpenAIRE, Crossref) would implement each method
- Used `...` (ellipsis) for protocol method bodies as per Python protocol convention

**Next steps:**
Ready to proceed with Task 1.4 - Implement the `BaseApiClient` with generic HTTP logic.

## 2025-06-25: Phase 1, Task 1.4 - BaseApiClient Completed

**What was done:**
- Created [`src/bibliofabric/client.py`](../../src/bibliofabric/client.py) with complete `BaseApiClient` implementation
- Extracted all generic HTTP client logic from the existing `AireloomClient`:
  - Complete `__init__` method accepting `BaseApiSettings`, `ResponseUnwrapper`, and `AuthStrategy`
  - Full `_request_with_retry` and `_execute_single_request` logic with comprehensive error handling
  - Client-side caching logic (`_generate_cache_key`, `_cache`) for GET requests
  - Rate limiting logic (`_parse_rate_limit_headers`, pre-request rate limit checks)
  - Session management and cleanup (`aclose`, `__aenter__`, `__aexit__`)
  - Pre/post request hooks execution
  - Authentication integration through `AuthStrategy` protocol
- Removed all OpenAIRE-specific parts:
  - Hardcoded base URLs (now passed as parameter)
  - Direct instantiation of resource clients (removed property methods)
  - OpenAIRE-specific constants and imports
- Updated [`src/bibliofabric/__init__.py`](../../src/bibliofabric/__init__.py) to include client and config modules in public API
- Used modern Python 3.13+ type hints throughout (`str | None`, `dict[str, Any]`, etc.)
- Maintained all existing functionality while making it completely generic

**Key decisions:**
- Made `base_url` a required parameter in `__init__` to maintain generic nature
- Kept the `ResponseUnwrapper` as a required parameter to enable API-agnostic response handling
- Maintained the same method signatures and behavior as the original `AireloomClient` for easy migration
- Used `NoAuth()` as default authentication strategy if none provided
- Preserved all error handling patterns and logging from the original implementation
- Made the client work with any API through the `ResponseUnwrapper` protocol abstraction

**Architecture benefits:**
- Complete separation between generic HTTP client logic and API-specific functionality
- Response unwrapping is now pluggable through the `ResponseUnwrapper` protocol
- Authentication is pluggable through the existing `AuthStrategy` protocol
- Caching, retries, rate limiting, and error handling are now reusable across all API clients
- The foundation is now in place for easy creation of new API clients (Crossref, OpenAlex, etc.)

**Next steps:**
Ready to proceed with Task 1.5 - Implement Generic Resource Mixins to complete the bibliofabric framework.

## 2025-06-25: Phase 2, Task 2.2 - AireloomClient & Config Refactored

**What was done:**
- Refactored [`src/aireloom/aireloom/config.py`](../../src/aireloom/aireloom/config.py) to inherit from bibliofabric:
  - Changed `ApiSettings` to inherit from `bibliofabric.config.BaseApiSettings`
  - Added back OpenAIRE-specific authentication fields: `openaire_api_token`, `openaire_client_id`, `openaire_client_secret`, `openaire_token_url`
  - Updated imports to use bibliofabric modules
  - Maintained OpenAIRE-specific env prefix (`AIRELOOM_`) and defaults
  - Override user agent to use OpenAIRE-specific default value
- Completely refactored [`src/aireloom/aireloom/client.py`](../../src/aireloom/aireloom/client.py) to inherit from bibliofabric:
  - Changed `AireloomClient` to inherit from `bibliofabric.client.BaseApiClient`
  - Dramatically simplified `__init__` method by delegating all generic logic to parent class
  - Instantiates `OpenAireUnwrapper` and passes it to `super().__init__()`
  - Maintains OpenAIRE-specific authentication logic and resource client instantiation
  - Reduced client code from ~838 lines to ~134 lines (84% reduction!)
  - Preserved all existing method signatures and behavior for backwards compatibility

**Key decisions:**
- Kept OpenAIRE authentication logic in the AireloomClient constructor for now, rather than moving it to a separate factory
- Maintained the same resource client property interface to ensure no breaking changes
- Used composition pattern: AireloomClient creates the unwrapper and passes it to the generic base
- Preserved all OpenAIRE-specific configuration while leveraging generic functionality from bibliofabric
- All generic HTTP logic (retries, caching, rate limiting, error handling) now comes from BaseApiClient

**Architecture benefits achieved:**
- AireloomClient is now focused purely on OpenAIRE-specific concerns
- All generic HTTP client functionality is reused from bibliofabric
- Clean separation between API-specific and generic functionality
- Foundation established for creating additional API clients (Crossref, OpenAlex, etc.) with minimal code
- Significant code reduction while maintaining full functionality

**Next steps:**
Ready to proceed with Task 2.3 - Refactor aireloom Resource Clients to use bibliofabric mixins (this requires Task 1.5 to be completed first).

## 2025-06-25: Phase 1, Task 1.5 - Generic Resource Mixins Completed

**What was done:**
- Created [`src/bibliofabric/resources.py`](../../src/bibliofabric/resources.py) with comprehensive mixin architecture (390 lines)
- Implemented `BaseResourceClient` class:
  - Holds reference to `BaseApiClient` for HTTP requests
  - Provides `response_unwrapper` property for accessing the API client's unwrapper
  - Defines abstract attributes for subclasses: `_entity_path`, `_entity_model`, `_search_response_model`
  - Includes proper initialization with debug logging
- Implemented `GettableMixin` for single entity retrieval:
  - Generic `get(entity_id)` method using search-with-ID pattern (since many APIs don't have direct GET endpoints)
  - Automatic Pydantic model parsing if `_entity_model` is defined
  - Comprehensive error handling with fallback to raw data if parsing fails
  - Uses response unwrapper for API-agnostic result extraction
- Implemented `SearchableMixin` for paginated search operations:
  - Generic `search(page, page_size, sort_by, filters)` method with flexible parameter handling
  - Support for both Pydantic model and dictionary filters with automatic conversion
  - Automatic response model parsing if `_search_response_model` is defined
  - Flexible parameter mapping (page-based pagination)
- Implemented `CursorIterableMixin` for cursor-based iteration:
  - Generic `iterate(page_size, sort_by, filters)` async generator for efficient large dataset traversal
  - Automatic cursor-based pagination handling using response unwrapper
  - Individual entity yielding with optional Pydantic model parsing
  - Robust pagination loop with proper termination conditions
- Created `ResourceClientProtocol` for type safety:
  - Defines interface expected by mixins using `typing.Protocol`
  - Ensures classes using mixins have required attributes and methods
  - Enables static type checking for mixin usage

**Key architectural decisions:**
- **Composable mixin design**: Resource clients can inherit from multiple mixins as needed for their specific functionality
- **Protocol-based type safety**: `ResourceClientProtocol` ensures compile-time verification of mixin requirements
- **API-agnostic response handling**: All mixins use the `ResponseUnwrapper` protocol for maximum flexibility across different API response formats
- **Graceful degradation**: Automatic fallback to raw data if Pydantic model parsing fails, with appropriate logging
- **Flexible filtering**: Support for both structured (Pydantic) and unstructured (dict) filter parameters
- **Cursor vs page pagination**: `CursorIterableMixin` uses cursor-based pagination for efficiency, while `SearchableMixin` uses page-based for direct access
- **Error boundary isolation**: Each mixin handles its own errors and converts them to `BibliofabricError` for consistent exception hierarchy
- **Modern Python features**: Extensive use of Python 3.13+ type hints, async generators, and structural subtyping

**Implementation benefits achieved:**
- **Significant code reduction potential**: Resource clients can now be implemented with just a few lines defining paths and models
- **Consistent API interface**: All API clients will have identical method signatures for common operations
- **Type safety**: Full static type checking support through protocols and modern type hints
- **Extensibility**: Easy to add new mixins for additional functionality (e.g., `UpdatableMixin`, `DeletableMixin`)
- **Testability**: Each mixin can be tested independently with mock implementations
- **Reusability**: Complete separation of concerns - HTTP logic, response unwrapping, and resource operations are all independent

**Phase 1 completion:**
With Task 1.5 completed, **Phase 1 is now fully complete**. The `bibliofabric` generic framework is ready with:
- Core modules (exceptions, logging, types, auth)
- Generic configuration (`BaseApiSettings`)
- Protocol definitions (`ResponseUnwrapper`)
- Generic HTTP client (`BaseApiClient`)
- Reusable resource mixins (`BaseResourceClient`, `GettableMixin`, `SearchableMixin`, `CursorIterableMixin`)

**Next steps:**
Ready to proceed with Phase 2, Task 2.3 - Refactor aireloom Resource Clients to use the new bibliofabric mixins.

## 2025-06-25: Phase 2, Task 2.3 - Resource Clients Refactored

**What was done:**
- Completely refactored all aireloom resource clients to use bibliofabric mixins:
  - **ResearchProductsClient**: Now inherits from `GettableMixin`, `SearchableMixin`, `CursorIterableMixin`, and `BaseResourceClient`. Reduced from ~270 lines to ~35 lines (87% reduction!)
  - **ProjectsClient**: Same mixin pattern, reduced from ~250+ lines to ~35 lines (86% reduction!)
  - **OrganizationsClient**: Same mixin pattern, reduced from ~270+ lines to ~35 lines (87% reduction!)
  - **DataSourcesClient**: Same mixin pattern, reduced from ~250+ lines to ~35 lines (86% reduction!)
  - **ScholixClient**: Kept custom logic for `search_links` and `iterate_links` methods due to unique Scholix API requirements (0-indexed pagination, different base URL, special parameter names), but simplified to inherit from `BaseResourceClient` only
- Fixed type compatibility issues between bibliofabric protocols and aireloom models by making `ResourceClientProtocol` more flexible with `typing.Any` for model attributes
- All resource clients now define only three class attributes:
  - `_entity_path`: The API endpoint path
  - `_entity_model`: The Pydantic model for individual entities
  - `_search_response_model`: The Pydantic model for search responses
- Removed all redundant implementations of `get()`, `search()`, and `iterate()` methods since they're now provided by mixins
- Preserved all existing method signatures and behaviors for complete backwards compatibility

**Key architectural decisions:**
- **Dramatic code reduction**: Resource clients went from 200-300 lines of complex implementation logic to just 30-40 lines of declarative configuration
- **Consistent API interface**: All standard resource clients now have identical `get()`, `search()`, and `iterate()` method implementations through mixins
- **Preserved custom logic**: ScholixClient maintains its unique pagination and API requirements while still benefiting from the base infrastructure
- **Type safety maintained**: Protocol-based type checking ensures all resource clients implement required attributes correctly
- **Zero breaking changes**: All existing method signatures and return types are preserved

**Benefits achieved:**
- **Massive code reduction**: Combined reduction of over 800 lines of duplicated logic across resource clients
- **Eliminated code duplication**: All common resource operations now use shared, tested implementations
- **Improved maintainability**: Bug fixes and enhancements in mixins automatically benefit all resource clients
- **Enhanced consistency**: Identical behavior patterns across all API endpoints
- **Future extensibility**: New API endpoints can be added with minimal boilerplate code

**Phase 2 completion:**
With Task 2.3 completed, **Phase 2 is now fully complete**. The aireloom package now:
- Inherits all generic HTTP functionality from `bibliofabric.BaseApiClient`
- Uses `bibliofabric.BaseApiSettings` for configuration with OpenAIRE-specific extensions
- Implements the `bibliofabric.ResponseUnwrapper` protocol via `OpenAireUnwrapper`
- Uses `bibliofabric` resource mixins for all standard CRUD operations
- Maintains all existing functionality while achieving 80%+ code reduction

**Next steps:**
Ready to proceed with Phase 3 - Validation by running the full test suite to ensure no functionality has been lost.

## 2025-06-25: Phase 3, Task 3.1 - Initial Test Run

**Issue identified:**
- Packages build successfully now (fixed README.md and Python version compatibility issues)
- All tests are failing with import errors: `ModuleNotFoundError: No module named 'bibliofabric'`
- The aireloom code is trying to import from old module structure (e.g., `from bibliofabric.auth import ...` instead of `from bibliofabric.auth import ...`)

**Root cause:**
The aireloom code hasn't been fully updated to use the new import structure. The tests and other aireloom modules still have imports pointing to the old module structure.

**Next immediate action:**
Need to update all import statements in aireloom to use bibliofabric for the generic modules (auth, exceptions, log_config, types) while keeping aireloom-specific imports for models, constants, etc.
