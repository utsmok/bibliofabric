# Implementation Plan: Refactoring AIREloom into `bibliofabric`

This plan breaks down the refactoring process into sequential, manageable steps. Each step is designed to be clear enough for a junior developer or an LLM assistant to execute.

### Phase 0: Project Setup

1.  **Create Directory Structure:**
    -   Create a directory `src` in the root of this workspace.
    -   Inside it, create two directories: `bibliofabric` and `aireloom`.
    -   Move the entire existing `aireloom` codebase into the new `src/aireloom` directory.

2.  **Initialize `bibliofabric` Project:**
    -   make sure the root `pyproject.toml` file is set up for the `bibliofabric` project and the correct folder (`src/bibliofabric`) is taken into account.
    -   The `pyproject.toml` should define the project `bibliofabric` and list its generic dependencies: `httpx`, `tenacity`, `pydantic`, `pydantic-settings`, `loguru`, `cachetools`, `python-dotenv`.

3.  **Update `aireloom` Project:**
    -   In the `aireloom/pyproject.toml`, add a local, editable dependency on `bibliofabric`:
        ```toml
        [project]
        # ... other settings
        dependencies = [
            # ... other dependencies
            "bibliofabric @ {root:uri}/../bibliofabric",
        ]
        ```

### Phase 1: Building `bibliofabric` (The Generic Framework)

1.  **Step 1.1: Migrate Foundational Modules**
    -   Copy `aireloom/exceptions.py` to `bibliofabric/exceptions.py`.
    -   Copy `aireloom/log_config.py` to `bibliofabric/log_config.py`.
    -   Copy `aireloom/types.py` to `bibliofabric/types.py`.
    -   Copy `aireloom/auth.py` to `bibliofabric/auth.py`. These modules are almost entirely generic and require minimal changes.

2.  **Step 1.2: Create Generic `BaseApiSettings`**
    -   Copy `aireloom/config.py` to `bibliofabric/config.py`.
    -   Rename `ApiSettings` to `BaseApiSettings`.
    -   Remove all OpenAIRE-specific fields: `openaire_api_token`, `openaire_client_id`, `openaire_client_secret`, `openaire_token_url`.

3.  **Step 1.3: Design and Implement the `ResponseUnwrapper` Protocol**
    -   Create a new file: `bibliofabric/models.py`.
    -   Define the `ResponseUnwrapper` protocol within this file as specified in the overview. It must include methods: `unwrap_results`, `unwrap_single_item`, `get_next_page_token`, and `get_total_results`.

4.  **Step 1.4: Create the `BaseApiClient`**
    -   Create a new file: `bibliofabric/client.py`.
    -   Define a class `BaseApiClient`.
    -   Copy the generic logic from the existing `aireloom/client.py` (`AireloomClient`) into `BaseApiClient`. This includes:
        -   The `__init__` method, refactored to accept a `BaseApiSettings` instance and a `ResponseUnwrapper` instance.
        -   The entire `_request_with_retry` and `_execute_single_request` logic.
        -   The caching logic (`_generate_cache_key`, `_cache`).
        -   The rate-limiting logic (`_parse_rate_limit_headers`, pre-request checks).
    -   Remove all OpenAIRE-specific parts, such as hardcoded base URLs and the direct instantiation of resource clients.

5.  **Step 1.5: Create Generic Resource Mixins**
    -   Create a new file: `bibliofabric/resources.py`.
    -   Define `BaseResourceClient` which simply holds a reference to the `BaseApiClient`.
    -   Define a `GettableMixin` with a generic `get(entity_id)` method that calls the API client and uses the unwrapper to return a single parsed item.
    -   Define a `CursorIterableMixin` with a generic `iterate()` method. This method will implement the pagination loop, calling the unwrapper to get results and the next token.
    -   Define a `SearchableMixin` with a generic `search()` method. This will handle page-based or offset-based search queries.

### Phase 2: Refactoring `aireloom` (The Specific Client)

1.  **Step 2.1: Implement `OpenAireUnwrapper`**
    -   Create a new file: `aireloom/unwrapper.py`.
    -   Define a class `OpenAireUnwrapper` that implements the `ResponseUnwrapper` protocol from `bibliofabric`.
        -   `unwrap_results` will return `response_json.get("results", [])`.
        -   `get_next_page_token` will return `response_json.get("header", {}).get("nextCursor")`.
        -   And so on for the other protocol methods.

2.  **Step 2.2: Refactor `aireloom` Configuration and Client**
    -   In `aireloom/config.py`, change `ApiSettings` to inherit from `bibliofabric.config.BaseApiSettings`.
    -   In `aireloom/client.py`, change `AireloomClient` to inherit from `bibliofabric.client.BaseApiClient`.
    -   The `AireloomClient.__init__` will now be very simple. It should instantiate the `OpenAireUnwrapper` and pass it to the `super().__init__()` call, along with the settings. It will also be responsible for instantiating its specific resource clients.

3.  **Step 2.3: Refactor `aireloom` Resource Clients**
    -   Go through each resource client file (e.g., `aireloom/resources/research_products_client.py`).
    -   Change the class signature to inherit from the appropriate mixins from `bibliofabric.resources` (e.g., `class ResearchProductsClient(GettableMixin, CursorIterableMixin, SearchableMixin, BaseResourceClient):`).
    -   Delete the now-redundant `get`, `iterate`, and `search` methods, as their logic is now in the mixins.
    -   Define the required class variables: `_entity_path`, `_entity_model`, and `_search_response_model`.
    -   Keep any truly API-specific methods (like the `ScholixClient`'s custom logic).

### Phase 3: Validation

1.  **Step 3.1: Run the Full Test Suite**
    -   Navigate to the root of the refactored `aireloom` project.
    -   Execute the `verification_script.py` and the `pytest` suite.
    -   `uvx pytest`

2.  **Step 3.2: Debug and Fix**
    -   Systematically address any test failures. Most issues will likely be related to incorrect data being passed between the generic core and the specific implementation (e.g., an error in the unwrapper or a mixin assumption).

### Phase 4: Prototyping (Post-Refactor)

1.  **Step 4.1: Create a `crossref-client` Project**
    -   Set up a new project directory alongside `aireloom` and `bibliofabric`.
    -   The goal is to see how quickly a new client can be scaffolded.

2.  **Step 4.2: Implement Crossref-specific Components**
    -   Define Pydantic models for Crossref items.
    -   Define `CrossrefUnwrapper`.
    -   Define a `WorksClient(GettableMixin, CursorIterableMixin, BaseResourceClient)` and see how little code is required.
