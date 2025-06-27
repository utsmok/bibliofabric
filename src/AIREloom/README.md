# AIREloom: An Asynchronous Python Client for OpenAIRE APIs

AIREloom provides a modern, asynchronous interface to interact with the OpenAIRE Graph API and Scholexplorer API. It is built upon the `bibliofabric` generic client framework, leveraging `httpx` and `pydantic` for robust and efficient data retrieval.

## Features

*   **Built on `bibliofabric`**: Inherits a generic, robust client foundation.
*   **Asynchronous by Design**: Utilizes `asyncio` and `httpx` for non-blocking API interactions.
*   **Comprehensive OpenAIRE Coverage**:
    *   OpenAIRE Graph API: Access to Research Products, Projects, Organizations, and Data Sources.
    *   Scholexplorer API: For discovering links (relationships) between scholarly entities.
*   **Robust Error Handling**: Built-in retry logic for transient network errors and common API error statuses.
*   **Flexible Authentication**:
    *   Automatic detection based on environment variables (`.env` file support).
    *   Supports No Authentication, Static API Token, and OAuth2 Client Credentials.
    *   Strategies provided by `bibliofabric.auth`.
*   **Data Validation & Modeling**: Uses Pydantic models for request parameters (filters) and for parsing API responses, ensuring data integrity and ease of use.
*   **Efficient Data Retrieval**:
    *   `get()`: Fetch single entities by ID.
    *   `search()`: Paginated search with filtering and sorting capabilities.
    *   `iterate()`: Efficiently iterate over large result sets using cursor-based pagination for Graph API endpoints and page-based for Scholix.
*   **Configurable Behavior**:
    *   Timeouts, retries, backoff factors through `bibliofabric.config.BaseApiSettings` and `aireloom.config.ApiSettings`.
    *   Optional client-side caching for GET requests.
    *   Rate limiting awareness and handling (parsing `Retry-After` headers).
*   **Extensible**: Basic hook system (pre/post-request) via `bibliofabric` for custom logic.

## Installation

AIREloom is designed to work with its companion library, `bibliofabric`. In a typical development setup for this project, both are local packages.

**1. `bibliofabric` (Generic Framework):**
   Ensure `bibliofabric` is available. If developing locally, it's usually a sibling directory.

**2. `aireloom` (This Library):**
   `aireloom` depends on the local `bibliofabric`. Its `pyproject.toml` should specify this:
   ```toml
   [project]
   # ...
   dependencies = [
       "bibliofabric @ {root:uri}/../bibliofabric",
       # other aireloom dependencies like pydantic, httpx, loguru...
   ]
   ```
   Install `aireloom` (and its local `bibliofabric` dependency) into your environment, preferably using `uv`:

```bash
# From the root of the monorepo or where both package dirs are visible
uv pip install -e src/bibliofabric -e src/AIREloom
# Or, if your project is set up with uv.workspace.json:
# uv sync
```

For end-users (if `aireloom` were published to PyPI), installation would be simpler:
```bash
# uv pip install aireloom
# (This would also pull bibliofabric if it were a PyPI dependency)

uv add aireloom
# or
> uv pip install aireloom
```


## Authentication

AIREloom automatically detects the authentication method based on your configuration (environment variables or `.env` file) unless you explicitly provide an `auth_strategy`.

**Environment Variables / `.env` file:**

Create a `.env` or `secrets.env` file in your project root. Prefix environment variables with `AIRELOOM_`.

*   **Static Token:** Set `AIRELOOM_OPENAIRE_API_TOKEN`.
    ```dotenv
    AIRELOOM_OPENAIRE_API_TOKEN="your_static_api_token_here"
    ```
*   **Client Credentials:** Set `AIRELOOM_OPENAIRE_CLIENT_ID` and `AIRELOOM_OPENAIRE_CLIENT_SECRET`. The token URL defaults to the standard OpenAIRE one but can be overridden with `AIRELOOM_OPENAIRE_TOKEN_URL`.
    ```dotenv
    AIRELOOM_OPENAIRE_CLIENT_ID="your_client_id_here"
    AIRELOOM_OPENAIRE_CLIENT_SECRET="your_client_secret_here"
    # AIRELOOM_OPENAIRE_TOKEN_URL="https://custom.token.url/oauth/token" # Optional override
    ```

**Explicit Strategy:**

You can pass an authentication strategy instance directly when creating `AireloomSession`.

```python
import asyncio
from aireloom import AireloomSession
from bibliofabric.auth import NoAuth, StaticTokenAuth, ClientCredentialsAuth

# 1. No Authentication
no_auth_session = AireloomSession(auth_strategy=NoAuth())

# 2. Static Token
token_auth_session = AireloomSession(auth_strategy=StaticTokenAuth(token="your_token"))

# 3. Client Credentials (reads ID/Secret/URL from env unless provided)
# Ensure AIRELOOM_OPENAIRE_CLIENT_ID and AIRELOOM_OPENAIRE_CLIENT_SECRET are set
cc_auth_session = AireloomSession(
    auth_strategy=ClientCredentialsAuth(
        client_id=None, # Provide directly, or reads from AIRELOOM_OPENAIRE_CLIENT_ID
        client_secret=None, # Provide directly, or reads from AIRELOOM_OPENAIRE_CLIENT_SECRET
        token_url=None # Provide directly, or reads from AIRELOOM_OPENAIRE_TOKEN_URL (defaults to OpenAIRE's)
    )
)

# If no strategy is provided, it defaults based on environment variables:
default_session = AireloomSession() # Will use CC if ID/Secret found, then Token, then NoAuth

async def main():
    # Use the session within an async context
    async with default_session as session:
        # ... make API calls ...
        print("Session created with default auth.")
        # Example: access research products client
        # products = await session.research_products.search(page_size=1)
        pass

# Example of running the main function
if __name__ == "__main__":
    asyncio.run(main())
```

## Basic Usage: `AireloomSession`

The primary way to interact with the APIs is through `AireloomSession`. It provides access to specific resource clients (e.g., `research_products`, `organizations`).

```python
import asyncio
from aireloom import AireloomSession
from bibliofabric.auth import NoAuth # Or other auth strategies
from bibliofabric.exceptions import BibliofabricError

async def run_example():
    # Initialize with desired auth strategy (or let it auto-detect)
    # Use async with for proper client setup and teardown
    async with AireloomSession(auth_strategy=NoAuth()) as session:
        # Example: Get a specific research product
        try:
            # Use a known OpenAIRE ID for a research product (replace with a real one for testing)
            product_id = "openaire____::doi:10.5281/zenodo.7664304" # Example, use a real ID
            print(f"Attempting to fetch product with ID: {product_id}")
            product = await session.research_products.get(product_id)
            print(f"Fetched Product: {product.title}")
            # Accessing the DOI from the pids list structure
            doi_value = None
            if product.pids:
                for pid in product.pids:
                    if pid.id and pid.id.scheme == "doi":
                        doi_value = pid.id.value
                        break
            print(f"  DOI: {doi_value if doi_value else 'Not available'}")
            # Accessing nested Pydantic model data safely
            print(f"  Type: {product.type if product.type else 'N/A'}")
            print(f"  Publication Date: {product.publicationDate if product.publicationDate else 'N/A'}")

        except BibliofabricError as e:
            print(f"An API or client error occurred: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(run_example())
```

## Detailed Usage Examples

For more detailed examples and explanations for each client (Research Products, Projects, Organizations, Data Sources, Scholix), please refer to the documentation in the `docs/usage/` directory:

*   [Research Products Usage](docs/usage/research_products.md)
*   [Projects Usage](docs/usage/projects.md)
*   [Organizations Usage](docs/usage/organizations.md)
*   [Data Sources Usage](docs/usage/data_sources.md)
*   [Scholix Links Usage](docs/usage/scholix.md)

## Retrieving Single Entities

Use the `get` method on the specific resource client (e.g., `session.research_products.get(...)`).

```python
import asyncio
from aireloom import AireloomSession
from bibliofabric.auth import NoAuth
from bibliofabric.exceptions import BibliofabricError, NotFoundError

async def get_entities():
    async with AireloomSession(auth_strategy=NoAuth()) as session:
        try:
            # Get Research Product by OpenAIRE ID (replace with a real one for testing)
            product_id = "openaire____::doi:10.5281/zenodo.7664304" # Example, use a real ID
            print(f"\nFetching Product ID: {product_id}")
            product = await session.research_products.get(product_id)
            # Extract DOI from pids structure
            doi_value = None
            if product.pids:
                for pid in product.pids:
                    if pid.id and pid.id.scheme == "doi":
                        doi_value = pid.id.value
                        break
            print(f"-> Product '{product.title}' fetched. DOI: {doi_value if doi_value else 'Not available'}")

            # Get Organization by OpenAIRE ID
            org_id = "openaire____::orgID:grid.5522.e" # Example: University of Twente (using a GRID ID format)
            print(f"\nFetching Organization ID: {org_id}")
            org = await session.organizations.get(org_id)
            print(f"-> Organization '{org.legalName}' fetched.")

            # Get Project by OpenAIRE ID (replace with a real one for testing)
            project_id = "corda_h2020::269f7314d3149ba797a079979839581b" # Example H2020 project ID format
            print(f"\nFetching Project ID: {project_id}")
            project = await session.projects.get(project_id)
            print(f"-> Project '{project.title}' fetched.")

            # Get Data Source by OpenAIRE ID
            source_id = "openaire____::datasourceId:doaj" # Example: Directory of Open Access Journals
            print(f"\nFetching Data Source ID: {source_id}")
            source = await session.data_sources.get(source_id)
            print(f"-> Data Source '{source.officialName}' fetched.")

        except NotFoundError as e:
            print(f"Error: Entity not found. {e}")
        except BibliofabricError as e:
            # Specific handling for other API errors
            print(f"Error fetching entity: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status Code: {e.response.status_code}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(get_entities())
```

## Searching Entities

Use the `search` method on the specific resource client. These support pagination, sorting, and filtering using Pydantic filter models.

```python
import asyncio
from aireloom import AireloomSession, NoAuth
from bibliofabric.exceptions import BibliofabricError, ValidationError
from aireloom.endpoints import ResearchProductsFilters, ProjectsFilters # Import filter models

async def search_entities():
    async with AireloomSession(auth_strategy=NoAuth()) as session:
        try:
            # Search Research Products (publications) with filters and sorting
            print("\nSearching Research Products...")
            rp_filters = ResearchProductsFilters( # Create filter model instance
                type="article",
                mainTitle="climate modelling", # Filter field name is mainTitle
                fromPublicationDate="2023-01-01",
                toPublicationDate="2023-12-31",
                # countryCode="NL", # Example country filter
            )
            search_response = await session.research_products.search(
                filters=rp_filters,
                page=1, # API is 1-indexed for page number in search
                page_size=5,
                sortBy="publicationDate desc" # Sort by publication date, newest first
            )

            print(f"Found {search_response.header.numFound} products matching criteria.")
            print(f"Showing page {search_response.header.pageNumber} of {search_response.header.totalPages} (page size {search_response.header.pageSize}):")
            if search_response.results:
                for product in search_response.results:
                    pub_date_str = product.publicationDate if product.publicationDate else "N/A"
                    # Extract DOI from pids structure
                    doi_value = None
                    if product.pids:
                        for pid in product.pids:
                            if pid.id and pid.id.scheme == "doi":
                                doi_value = pid.id.value
                                break
                    print(f"- {product.title} ({pub_date_str}) - DOI: {doi_value if doi_value else 'Not available'}")
            else:
                print("No products found for this page/filter combination.")

            # Search Projects
            print("\nSearching Projects...")
            proj_filters = ProjectsFilters(keywords=["artificial intelligence"], fundingShortName="EC") # Filter by keyword(s) and funder short name
            project_response = await session.projects.search(
                filters=proj_filters,
                page=1,
                page_size=3,
                sortBy="endDate desc" # Sort by end date, newest first
            )
            print(f"Found {project_response.header.numFound} projects.")
            if project_response.results:
                for project in project_response.results:
                    print(f"- {project.title} (Acronym: {project.acronym}, ID: {project.id})")
            else:
                print("No projects found.")

        except ValidationError as e:
            print(f"Invalid search parameters: {e}")
        except BibliofabricError as e:
            print(f"API Error during search: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during search: {e}")

if __name__ == "__main__":
    asyncio.run(search_entities())
```

**Filtering:** Instantiate the appropriate Pydantic filter model (e.g., `ResearchProductsFilters` from `aireloom.endpoints`) and pass it to the `filters` parameter of the `search` method. Valid filter fields are defined in these models.

**Sorting:** Use the `sortBy` parameter with the format `"field_name asc"` or `"field_name desc"`. Valid sort fields depend on the entity type (e.g., `publicationDate` for research products, `endDate` for projects). An invalid sort field raises a `ValidationError`.

**Pagination:** Use the `page` (1-indexed for Graph API) and `page_size` parameters. The response object (`<EntityType>Response`) contains a `header` attribute with pagination information (`pageNumber`, `pageSize`, `numFound` results, `totalPages`, `nextCursor`, etc.).

## Iterating Through All Results

For retrieving all results matching criteria without manual pagination, use the `iterate` method on the specific resource client. These use efficient cursor-based pagination provided by the API for Graph API endpoints.

```python
import asyncio
from aireloom import AireloomSession, NoAuth
from bibliofabric.exceptions import BibliofabricError, ValidationError
from aireloom.endpoints import ResearchProductsFilters # Import filter model

async def iterate_all_results():
    async with AireloomSession(auth_strategy=NoAuth()) as session:
        print("\nIterating through recent Peer Reviewed articles from NL...")
        count = 0
        max_results_to_fetch = 15 # Limit for example purposes
        try:
            # Iterate through publications from the Netherlands, newest first
            rp_filters = ResearchProductsFilters(
                countryCode="NL",
                type="article",
                fromPublicationDate="2023-01-01",
                toPublicationDate="2023-12-31",
                isPeerReviewed=True
            )
            async for product in session.research_products.iterate(
                filters=rp_filters,
                page_size=5, # How many to fetch per underlying API call (adjust as needed)
                sortBy="publicationDate desc" # Get newest first
            ):
                count += 1
                pub_date_str = product.publicationDate if product.publicationDate else "N/A"
                print(f"#{count}: {product.title} ({pub_date_str})")
                if count >= max_results_to_fetch:
                    print(f"\nStopping iteration early after fetching {max_results_to_fetch} results.")
                    break
            print(f"\nFinished iterating. Total fetched in this run: {count}")

        except ValidationError as e:
            print(f"Invalid parameters for iteration: {e}")
        except BibliofabricError as e:
            print(f"API Error during iteration: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during iteration: {e}")

if __name__ == "__main__":
    asyncio.run(iterate_all_results())
```

**Note:** Iteration fetches results in batches (`page_size`) using the API's cursor mechanism (for Graph API) or page-based mechanism (for Scholix) until all matching entities are retrieved or the iteration is explicitly broken.

## Working with Scholexplorer (Scholix Links)

Use `session.scholix.search_links` or `session.scholix.iterate_links` to find relationships (links) between research products.

**Important:** You *must* provide either `sourcePid` or `targetPid` in the `ScholixFilters` model for Scholix searches. PIDs should typically be DOIs or other persistent identifiers recognized by Scholexplorer, prefixed with their scheme (e.g., `doi:10.5281/zenodo.xxxxxx`).

```python
import asyncio
from aireloom import AireloomSession, NoAuth
from bibliofabric.exceptions import BibliofabricError, ValidationError
from aireloom.endpoints import ScholixFilters # Import filter model

async def search_scholix():
    async with AireloomSession(auth_strategy=NoAuth()) as session:
        print("\nSearching Scholix links...")
        try:
            # Find links where a specific DOI is the source
            source_doi_val = "10.1038/s41586-021-03964-9" # Example Nature paper DOI
            print(f"Searching for links originating from PID: doi:{source_doi_val}")

            s_filters_source = ScholixFilters(
                sourcePid=f"doi:{source_doi_val}", # Ensure PID is prefixed with scheme
                # targetType="Dataset", # Example additional filter
                relation="References" # Example: source references target
            )
            scholix_response = await session.scholix.search_links(
                filters=s_filters_source,
                page=0, # Scholexplorer uses 0-based pagination for 'page'
                page_size=10 # Corresponds to 'rows' parameter in Scholexplorer
            )

            print(f"Found {scholix_response.total_links} links originating from PID: doi:{source_doi_val} (showing page {scholix_response.current_page + 1} of {scholix_response.total_pages}).")
            if scholix_response.result:
                for link in scholix_response.result:
                    target_id = link.target.identifier[0].id_val if link.target.identifier else 'N/A'
                    target_type = link.target.type if link.target else 'N/A'
                    print(f"- Relation: {link.relationship_type.name if link.relationship_type else 'N/A'} -> Target: {target_id} ({target_type})")
            else:
                print("No links found for this source PID on this page.")

            # Example: Find links targeting a specific PID
            target_doi_val = "10.5281/zenodo.3937230" # Example Zenodo dataset DOI
            print(f"\nSearching for links targeting PID: doi:{target_doi_val}")
            s_filters_target = ScholixFilters(targetPid=f"doi:{target_doi_val}")
            scholix_target_response = await session.scholix.search_links(
                filters=s_filters_target,
                page_size=5
            )
            print(f"Found {scholix_target_response.total_links} links targeting doi:{target_doi_val}.")
            if scholix_target_response.result:
                 for link in scholix_target_response.result:
                    source_id = link.source.identifier[0].id_val if link.source.identifier else 'N/A'
                    source_type = link.source.type if link.source else 'N/A'
                    print(f"- Source: {source_id} ({source_type}) -> Relation: {link.relationship_type.name if link.relationship_type else 'N/A'}")
            else:
                print("No links found targeting this PID.")


        except ValueError as ve: # e.g., missing sourcePid/targetPid
             print(f"Validation Error: {ve}")
        except ValidationError as ve: # Pydantic validation error
             print(f"Invalid Scholix filter parameter: {ve}")
        except BibliofabricError as e:
            print(f"API Error searching Scholix: {e}")
        except Exception as e:
            print(f"An unexpected error occurred searching Scholix: {e}")

if __name__ == "__main__":
    asyncio.run(search_scholix())
```

## Error Handling

AIREloom raises specific exceptions found in `bibliofabric.exceptions`:

*   `BibliofabricError`: Base exception for the library.
*   `APIError`: For non-success HTTP status codes (4xx, 5xx) from the API after retries. Contains the `response` and `request` objects.
*   `NotFoundError`: Subclass of `APIError` for 404 status codes.
*   `RateLimitError`: Subclass of `APIError` specifically for 429 status codes.
*   `TimeoutError`: For request timeouts after retries. Contains the `request` object.
*   `NetworkError`: For connection errors after retries. Contains the `request` object.
*   `AuthError`: For authentication failures (e.g., invalid credentials, token fetch failure).
*   `ConfigurationError`: For missing required configuration (e.g., missing token for `StaticTokenAuth`).
*   `ValidationError`: For invalid filter/sort parameters provided by the user, or Pydantic model validation failures.

Wrap API calls in `try...except` blocks to handle potential issues gracefully.

```python
import asyncio
from aireloom import AireloomSession, NoAuth
from bibliofabric.exceptions import (
    BibliofabricError, APIError, NotFoundError, RateLimitError, TimeoutError, NetworkError, AuthError, ValidationError
)
from aireloom.endpoints import ResearchProductsFilters

async def error_handling_example():
    async with AireloomSession(auth_strategy=NoAuth()) as session:
        try:
            # Intentionally use an invalid filter key by trying to pass it directly
            # This will now be caught by Pydantic in ResearchProductsFilters if not a valid field
            print("\nAttempting search with invalid filter structure (should be caught by Pydantic)...")
            # Correct way is to use the Pydantic model:
            # rp_filters = ResearchProductsFilters(some_invalid_filter_key="some_value") # This would fail at Pydantic model creation
            # await session.research_products.search(filters=rp_filters)
            # Forcing an error by passing an invalid type to filters:
            await session.research_products.search(filters="this is not a filter model") # type: ignore
        except TypeError as e: # Pydantic model_dump or validation might raise TypeError or ValidationError
            print(f"Caught expected error due to invalid filter type: {e}")
        except ValidationError as e: # If filters was a dict with invalid keys for the Pydantic model
            print(f"Caught expected validation error for filters: {e}")
        except Exception as e:
            print(f"Caught unexpected error during invalid search: {e}")

        try:
            # Intentionally use a non-existent ID
            print("\nAttempting to fetch non-existent ID...")
            await session.research_products.get("openaire____::doi:10.xxxx/nonexistent")
        except NotFoundError as e:
            print(f"Caught expected NotFoundError: {e}")
        except APIError as e:
            print(f"Caught other API error: Status {e.response.status_code if e.response else 'N/A'}")
        except BibliofabricError as e:
            print(f"Caught other Aireloom error: {e}")
        except Exception as e:
            print(f"Caught unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(error_handling_example())
```

## Advanced Usage

*   **Custom `httpx.AsyncClient`:** While `AireloomSession` manages its own internal `AireloomClient` (which in turn manages an `httpx.AsyncClient`), you can instantiate `AireloomClient` directly if you need to pass a pre-configured `httpx.AsyncClient` for fine-grained control over transport, proxies, event hooks, etc.
*   **Override Settings:** You can configure client behavior (timeout, retries) via environment variables (see Authentication section) or by passing an `ApiSettings` instance when creating an `AireloomClient`.
*   **Direct Client Use:** You can use `AireloomClient` directly for making requests. This gives you the raw `httpx.Response` object. You would be responsible for parsing the JSON response and potentially validating it against Pydantic models yourself. The resource clients (e.g., `client.research_products`) are available on the `AireloomClient` instance.

```python
import asyncio
import httpx
from aireloom.client import AireloomClient
from bibliofabric.auth import NoAuth
from aireloom.config import ApiSettings
from aireloom.endpoints import ResearchProductsFilters

# Example: Using a custom httpx client via AireloomClient
async def use_direct_client_with_custom_httpx():
    # Configure custom httpx settings
    limits = httpx.Limits(max_connections=10, max_keepalive_connections=5)
    custom_http_client = httpx.AsyncClient(limits=limits, timeout=45.0)

    # Create AireloomClient, passing the custom httpx client
    custom_settings = ApiSettings(request_timeout=45.0) # Match timeout if desired
    async with AireloomClient(
        auth_strategy=NoAuth(),
        http_client=custom_http_client,
        settings=custom_settings
    ) as client: # client is an AireloomClient instance
        try:
            print("\nMaking request with direct client's resource client and custom httpx client...")
            # Access resource client from AireloomClient instance
            rp_filters = ResearchProductsFilters(type="dataset", mainTitle="soil data")
            response_model = await client.research_products.search(filters=rp_filters, page_size=1) # page defaults to 1
            print(f"Direct client (via resource client) response: Found {response_model.header.numFound} datasets.")
            if response_model.results:
                print(f"First dataset: {response_model.results[0].title}")

            # Example of using client.request directly (less common for end-users, returns raw httpx.Response or parsed model)
            # raw_response_or_model = await client.request("GET", "researchProducts", params={"pageSize": 1, "type": "dataset"})
            # print(f"Raw response status: {raw_response.status_code}")

        except Exception as e:
            print(f"Error using direct client: {e}")
    # Remember to close the client you created manually if you passed it in
    # AireloomClient will close httpx.AsyncClient instances it creates itself.
    # If you pass an external client, you are responsible for its lifecycle.
    if not custom_http_client.is_closed:
        await custom_http_client.aclose()
        print("Manually closed custom httpx client.")

if __name__ == "__main__":
    asyncio.run(use_direct_client_with_custom_httpx())

```

*   **Hook System:** AIREloom includes a basic hook system allowing you to execute custom functions before a request is sent (pre-request hooks) and after a response is received (post-request hooks). This can be used for custom logging, modifying request parameters/headers, or reacting to responses. For more details, see the [Hook System Documentation](docs/advanced/hooks.md).

## Dev

This project uses `uv` for environment and dependency management.

```bash
> git clone github.com/utsmok/aireloom.git
> cd aireloom
> uv init
> uv sync --all-extras
```

run tests with `uv pytest`, format / lint with `uvx ruff format .` and `uvx ruff check --fix .`.


Contributions are welcome! Please follow standard practices like creating issues for bugs or feature requests, submitting pull requests with relevant tests, and adhering to the coding style enforced by Ruff (use `uvx ruff format .` and `uvx ruff check --fix .`).

## License

This project is licensed under the MIT License.
