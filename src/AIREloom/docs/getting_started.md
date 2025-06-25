# Getting Started with AIREloom

This guide will walk you through the basic steps to get AIREloom up and running, from installation to making your first API calls.

## 1. Installation

First, you need to install AIREloom. We recommend using `uv` or `pip`. For detailed instructions, please see the [Installation Guide](installation.md).

```bash
# Using uv
uv pip install aireloom

# Or using pip
pip install aireloom
```

## 2. Authentication

AIREloom needs to authenticate with the OpenAIRE APIs for most operations. You have several options:

*   **No Authentication:** For accessing publicly available data.
*   **Static API Token:** If you have an API token from OpenAIRE.
*   **OAuth2 Client Credentials:** For applications that need to access protected resources.

For this getting started guide, we'll assume you are either accessing public data (NoAuth) or have a Static API Token.

### Setting up a Static API Token (Optional)

If you have an OpenAIRE API token, the easiest way to configure it is by setting an environment variable. Create a file named `.env` in your project's root directory and add the following line:

```dotenv
# .env file
AIRELOOM_OPENAIRE_API_TOKEN="your_openaire_api_token_here"
```

AIREloom will automatically pick this up. If you don't set this and don't explicitly choose `NoAuth`, AIREloom might default to `NoAuth` or try other methods if configured.

For more details on all authentication methods, see the [Authentication Guide](authentication.md).

## 3. Your First AIREloom Script

Let's write a simple asynchronous script to interact with the OpenAIRE API.

```python
import asyncio
from aireloom import AireloomSession
from bibliofabric.auth import NoAuth # Or StaticTokenAuth if you have a token
from bibliofabric.exceptions import BibliofabricError, APIError
from aireloom.endpoints import ResearchProductsFilters # For searching

# --- Configuration ---
# For this example, we'll explicitly use NoAuth.
# If you have set AIRELOOM_OPENAIRE_API_TOKEN in your .env file,
# you could also omit the auth_strategy or use StaticTokenAuth().
AUTH_STRATEGY = NoAuth()
# Replace with a known OpenAIRE ID for a research product (e.g., a DOI)
# Ensure it's in the OpenAIRE ID format: "openaire____::doi:YOUR_DOI_HERE"
# Example using a Zenodo record:
EXAMPLE_PRODUCT_ID = "openaire____::doi:10.5281/zenodo.7664304"


async def main():
    # Initialize AireloomSession using an async context manager
    async with AireloomSession(auth_strategy=AUTH_STRATEGY) as session:
        print(f"AIREloom session initialized with: {type(session._client._auth_strategy).__name__}")

        # --- 1. Fetching a Single Entity ---
        print(f"\nAttempting to fetch research product with ID: {EXAMPLE_PRODUCT_ID}")
        try:
            product = await session.research_products.get(EXAMPLE_PRODUCT_ID)
            print(f"Successfully fetched product!")
            print(f"  Title: {product.title}")
            doi = product.get_pid_value('doi')
            print(f"  DOI: {doi if doi else 'N/A'}")
            # Accessing type and publication date (attributes might vary based on actual model structure)
            print(f"  Type: {product.originaltype.attrs.get('classname') if product.originaltype and product.originaltype.attrs else 'N/A'}")
            print(f"  Publication Date: {product.dateofacceptance.value if product.dateofacceptance else 'N/A'}")

        except APIError as e:
            if e.response and e.response.status_code == 404:
                print(f"  Error: Product with ID {EXAMPLE_PRODUCT_ID} not found (404).")
            else:
                print(f"  API Error fetching product: {e} (Status: {e.response.status_code if e.response else 'N/A'})")
        except BibliofabricError as e:
            print(f"  Aireloom Error fetching product: {e}")
        except Exception as e:
            print(f"  An unexpected error occurred: {e}")


        # --- 2. Searching for Entities ---
        print("\nAttempting to search for research products (e.g., articles about 'climate change')...")
        try:
            # Define search filters
            # Note: Available filter fields depend on the endpoint and are defined in Pydantic models
            # in aireloom.endpoints. For ResearchProducts, 'title' can be used for keyword search in title.
            # 'type' can be 'article', 'dataset', etc.
            rp_filters = ResearchProductsFilters(
                title="climate change",
                type="article",
                publicationYear="2023" # Example: filter by year
            )

            # Perform the search
            search_response = await session.research_products.search(
                filters=rp_filters,
                page=1,      # Page number (1-indexed)
                page_size=3  # Number of results per page
            )

            print(f"Search successful. Found {search_response.header.total} total matching products.")
            print(f"Displaying page {search_response.header.page} of {search_response.header.totalPages}:")

            if search_response.results:
                for i, item in enumerate(search_response.results):
                    print(f"  Result {i+1}:")
                    print(f"    Title: {item.title}")
                    item_doi = item.get_pid_value('doi')
                    print(f"    DOI: {item_doi if item_doi else 'N/A'}")
                    print(f"    Publication Date: {item.dateofacceptance.value if item.dateofacceptance else 'N/A'}")
            else:
                print("  No products found for this page/filter combination.")

        except BibliofabricError as e:
            print(f"  Aireloom Error during search: {e}")
        except Exception as e:
            print(f"  An unexpected error occurred during search: {e}")


        # --- 3. Iterating Through All Results (Brief Mention) ---
        # For retrieving all results matching criteria without manual pagination,
        # you can use the `iterate()` method.
        # print("\nIterating through some results (example)...")
        # count = 0
        # try:
        #     async for item in session.research_products.iterate(filters=rp_filters, page_size=5, sortBy="dateofacceptance,desc"):
        #         count += 1
        #         print(f"  Iterated item #{count}: {item.title}")
        #         if count >= 5: # Limit for this example
        #             print("  (Stopping iteration early for example)")
        #             break
        # except Exception as e:
        #     print(f"  Error during iteration: {e}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Running the Script

1.  Save the code above as a Python file (e.g., `openaire_test.py`).
2.  Ensure you have an internet connection.
3.  If you're using a Static API Token, make sure your `.env` file is in the same directory or the environment variable is set.
4.  Run the script from your terminal:

    ```bash
    python openaire_test.py
    ```

You should see output indicating the session initialization, the result of fetching a single product, and the results of your search query.

## Key Takeaways

*   **`AireloomSession`:** The main entry point for interacting with the API. Use it as an asynchronous context manager (`async with`).
*   **Resource Clients:** Access specific API endpoints via attributes on the session (e.g., `session.research_products`, `session.projects`).
*   **`get()` method:** Retrieves a single entity by its ID.
*   **`search()` method:** Searches for entities based on filters, with pagination.
    *   Filter parameters are passed using Pydantic models from `aireloom.endpoints`.
*   **`iterate()` method:** (Briefly shown) Efficiently retrieves all results for a query, handling pagination automatically.
*   **Asynchronous Operations:** All API calls are `async` and need to be `await`ed.
*   **Pydantic Models:** API responses are parsed into Pydantic models, providing type-hinted and easy-to-access data.
*   **Error Handling:** Wrap API calls in `try...except` blocks to catch potential `BibliofabricError` exceptions or more specific ones like `APIError`.

## Next Steps

This guide provided a basic introduction. To explore AIREloom further:

*   Dive into the detailed **Usage Guides** for each resource type:
    *   [Research Products](usage/research_products.md)
    *   [Projects](usage/projects.md)
    *   [Organizations](usage/organizations.md)
    *   [Data Sources](usage/data_sources.md)
    *   [Scholix Links](usage/scholix.md)
*   Learn about advanced topics:
    *   [Configuration](advanced/configuration.md)
    *   [Rate Limiting](advanced/rate_limiting.md)
    *   [Caching](advanced/caching.md)
    *   [Request Hooks](advanced/hooks.md)
    *   [Error Handling](advanced/error_handling.md)

Happy data fetching!
