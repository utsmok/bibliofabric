# Error Handling

AIREloom uses a hierarchy of custom exceptions to signal various issues that can occur during API interactions, configuration, or client-side validation. Understanding these exceptions is key to building robust applications.

All AIREloom-specific exceptions inherit from `BibliofabricError`.

## Exception Hierarchy and Details

Here are the main exceptions you might encounter:

*   **`BibliofabricError(Exception)`**:
    *   The base class for all errors raised by the AIREloom library.
    *   Attributes:
        *   `message` (str): The primary error message.
        *   `response` (Optional[`httpx.Response`]): The `httpx.Response` object if the error is related to an API response.
        *   `request` (Optional[`httpx.Request`]): The `httpx.Request` object associated with the error, if available.

*   **`APIError(BibliofabricError)`**:
    *   Represents a generic error returned by the OpenAIRE API, typically corresponding to non-success HTTP status codes (4xx or 5xx) that are not covered by more specific exceptions below.
    *   Inherits `message`, `response`, and `request` from `BibliofabricError`.

*   **`NotFoundError(APIError)`**:
    *   A specific type of `APIError` raised when the API returns a `404 Not Found` status, indicating that the requested resource does not exist.

*   **`ValidationError(BibliofabricError)`**:
    *   Raised for several reasons:
        *   Client-side validation failure before sending a request (e.g., invalid filter parameters, incorrect sort field format).
        *   API response indicating a validation error, often a `400 Bad Request` or `422 Unprocessable Entity`.
    *   The `response` attribute might be present if the error originated from an API response.

*   **`RateLimitError(APIError)`**:
    *   A specific type of `APIError` raised when the API returns a `429 Too Many Requests` status, indicating that your application has exceeded its allocated rate limit.
    *   See the [Rate Limiting Guide](rate_limiting.md) for how AIREloom handles these.

*   **`TimeoutError(BibliofabricError)`**:
    *   Raised when a request to the API times out after exhausting configured retries.
    *   The `response` attribute will typically be `None`.
    *   The `request` attribute will contain the `httpx.Request` object that timed out.

*   **`NetworkError(BibliofabricError)`**:
    *   Raised for network-level issues that prevent communication with the API, such as DNS resolution failures, connection refused, or other `httpx.NetworkError` subtypes.
    *   The `response` attribute will typically be `None`.
    *   The `request` attribute will contain the `httpx.Request` object that failed.

*   **`ConfigurationError(BibliofabricError)`**:
    *   Raised if there's an issue with the AIREloom client's configuration (e.g., missing required settings for an authentication strategy).
    *   Typically does not have `response` or `request` attributes.

*   **`AuthError(BibliofabricError)`**:
    *   Raised when an authentication-specific error occurs. This could be due to:
        *   Failure to obtain an OAuth2 token (e.g., invalid client credentials).
        *   An API response indicating an authentication or authorization failure (e.g., `401 Unauthorized`, `403 Forbidden`).
    *   The `response` attribute may be present if the error was triggered by an API response.

## Handling Exceptions

It's crucial to wrap your AIREloom API calls in `try...except` blocks to gracefully handle potential errors. You can catch specific exceptions or the general `BibliofabricError`.

```python
import asyncio
import httpx # For type hinting if needed
from aireloom import AireloomSession
from bibliofabric.auth import NoAuth # Or your preferred auth strategy
from bibliofabric.exceptions import (
    BibliofabricError,
    APIError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    TimeoutError,
    NetworkError,
    AuthError,
    ConfigurationError
)
# Assuming ResearchProductsFilters is imported for a search example
from aireloom.endpoints import ResearchProductsFilters


async def fetch_data_example():
    # Using NoAuth for simplicity in this example.
    # Ensure your auth strategy is correctly configured for actual use.
    async with AireloomSession(auth_strategy=NoAuth()) as session:
        try:
            # Example 1: Fetching a single entity
            print("Attempting to fetch a specific product...")
            # Replace with a valid ID for testing, or an invalid one to trigger NotFoundError
            product = await session.research_products.get("openaire____::doi:10.5281/zenodo.7664304")
            print(f"Fetched product: {product.title}")

            # Example 2: Searching with potentially invalid filters
            print("\nAttempting a search...")
            # To trigger ValidationError client-side, pass an invalid filter type:
            # invalid_filters = "this_is_not_a_filter_model"
            # Or use a filter model with invalid field values if server-side validation is targeted
            search_filters = ResearchProductsFilters(title="modern research trends", publicationYear="2023")
            search_results = await session.research_products.search(filters=search_filters, page_size=2)
            print(f"Found {search_results.header.total} search results.")

        except NotFoundError as e:
            print(f"Resource not found: {e.message}")
            if e.request:
                print(f"  Request URL: {e.request.url}")

        except ValidationError as e:
            print(f"Validation error: {e.message}")
            if e.response:
                print(f"  API Response Status: {e.response.status_code}")
                # You might want to log e.response.text for more details from the API
                print(f"  API Response Text: {e.response.text[:200]}...")
            if e.request:
                 print(f"  Request URL: {e.request.url}")


        except RateLimitError as e:
            print(f"Rate limit exceeded: {e.message}")
            if e.response and "Retry-After" in e.response.headers:
                print(f"  Suggested Retry-After: {e.response.headers['Retry-After']} seconds")
            # Implement your own delay or backoff strategy if needed beyond client's retries

        except TimeoutError as e:
            print(f"Request timed out: {e.message}")
            if e.request:
                print(f"  Timed out request URL: {e.request.url}")

        except NetworkError as e:
            print(f"Network error: {e.message}")
            if e.request:
                print(f"  Failed request URL: {e.request.url}")

        except AuthError as e:
            print(f"Authentication error: {e.message}")
            # Check e.response for details if it's an API auth error

        except APIError as e: # Catch other API errors (e.g., 500 Internal Server Error)
            print(f"Generic API error: {e.message}")
            if e.response:
                print(f"  Status: {e.response.status_code}, URL: {e.request.url if e.request else 'N/A'}")
                print(f"  Response: {e.response.text[:200]}...")

        except ConfigurationError as e:
            print(f"Configuration error: {e.message}")

        except BibliofabricError as e: # Catch-all for any other Aireloom specific errors
            print(f"An Aireloom error occurred: {e.message}")
            if e.response:
                print(f"  Status: {e.response.status_code}, URL: {e.request.url if e.request else 'N/A'}")
            elif e.request:
                print(f"  Request URL: {e.request.url}")

        except Exception as e: # Catch any other unexpected errors
            print(f"An unexpected non-Aireloom error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(fetch_data_example())
```

## Best Practices

*   **Be Specific:** Catch the most specific exceptions you anticipate first (e.g., `NotFoundError`, `RateLimitError`), followed by more general ones like `APIError`, and finally `BibliofabricError`.
*   **Inspect `response` and `request`:** For errors like `APIError`, the `response` attribute can provide valuable details from the API (status code, headers, body). The `request` attribute helps identify which call failed.
*   **Logging:** In a production application, log detailed error information, including stack traces and the content of `request` and `response` objects, to help diagnose issues.
*   **User Feedback:** Provide clear feedback to users when errors occur, especially for issues like timeouts or resources not being found.
*   **Retry Strategies:** While AIREloom has built-in retries for transient errors and rate limits, you might implement additional application-level retry logic for certain scenarios, perhaps with longer or more complex backoff strategies.

By effectively handling these exceptions, you can create more resilient and user-friendly applications that interact with OpenAIRE APIs.
