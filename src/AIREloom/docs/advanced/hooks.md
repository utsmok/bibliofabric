# Request Hooks

AIREloom provides a hook system that allows you to inject custom logic into the request/response lifecycle. This is useful for tasks like custom logging, modifying request parameters or headers, or performing custom actions based on API responses.

Hooks are functions (or any callable) that you define and then register with the AIREloom client via `ApiSettings`.

## Types of Hooks

There are two types of hooks available:

1.  **Pre-request Hooks (`pre_request_hooks`):**
    *   Executed *before* an HTTP request is sent to the API.
    *   Can be used to inspect or modify the `httpx.Request` object.
    *   Useful for adding custom headers, logging request details, or even altering the request URL or body if necessary (though direct modification of the request body should be done with caution).

2.  **Post-request Hooks (`post_request_hooks`):**
    *   Executed *after* an HTTP response has been received from the API and *after* it has been parsed into a Pydantic model (if applicable and successful).
    *   Receives the `httpx.Response` object and, if parsing was successful and a Pydantic model is expected, the parsed Pydantic model instance. If parsing fails or no model is expected (e.g., for raw responses), the model argument might be `None` or an exception instance.
    *   Useful for custom logging of responses, metrics collection, or triggering actions based on response content or status.

## Defining Hook Functions

### Pre-request Hook Signature

A pre-request hook function should generally accept an `httpx.Request` object as its argument. It typically does not need to return anything, but if it does, the return value is ignored.

```python
import httpx

def my_pre_request_logger(request: httpx.Request) -> None:
    print(f"Outgoing request: {request.method} {request.url}")
    print(f"  Headers: {request.headers}")
    # You could modify headers here, for example:
    # request.headers["X-Custom-Header"] = "MyValue"

def another_pre_hook(request: httpx.Request) -> None:
    # Another pre-request action
    pass
```

### Post-request Hook Signature

A post-request hook function should generally accept the `httpx.Response` object and an optional second argument for the parsed Pydantic model. The model argument might be `None` if the response was not parsed into a model (e.g., raw response or an error occurred before parsing).

```python
import httpx
from pydantic import BaseModel # Or your specific AIREloom models
from typing import Any, Optional

def my_post_request_logger(response: httpx.Response, parsed_model: Optional[Any]) -> None:
    print(f"Received response: {response.status_code} from {response.url}")
    print(f"  Response Headers: {response.headers}")
    if parsed_model:
        print(f"  Parsed Model Type: {type(parsed_model)}")
        # Example: if parsed_model is an instance of a known Pydantic model
        # if isinstance(parsed_model, YourExpectedModel):
        #     print(f"  Model content: {parsed_model.model_dump_json(indent=2)}")
    elif response.status_code >= 400:
        print(f"  Response Content (Error): {response.text[:200]}...") # Log snippet of error

def another_post_hook(response: httpx.Response, parsed_model: Optional[Any]) -> None:
    # Another post-request action
    if response.status_code == 200 and parsed_model:
        # Perform action on successful, parsed response
        pass
```
*Note: The exact type hint for `parsed_model` can be `Optional[BaseModel]` if you expect Pydantic models, or `Optional[Any]` for more generality.*

## Registering Hooks

Hooks are registered by providing lists of these callable functions to the `ApiSettings` object when initializing `AireloomSession` or `AireloomClient`.

```python
import asyncio
from aireloom import AireloomSession
from aireloom.config import ApiSettings
from bibliofabric.auth import NoAuth # Or your preferred auth strategy

# --- Define your hook functions (as above) ---
# def my_pre_request_logger(request: httpx.Request) -> None: ...
# def my_post_request_logger(response: httpx.Response, parsed_model: Optional[Any]) -> None: ...


async def main():
    custom_settings = ApiSettings(
        pre_request_hooks=[my_pre_request_logger, another_pre_hook],
        post_request_hooks=[my_post_request_logger, another_post_hook]
    )

    async with AireloomSession(settings=custom_settings, auth_strategy=NoAuth()) as session:
        print("Session with hooks initialized. Making a request...")
        try:
            # Example: Fetch a research product
            # Your hooks will be called before and after this request.
            product = await session.research_products.get("openaire____::doi:10.5281/zenodo.7664304")
            if product:
                print(f"\nSuccessfully fetched product via session: {product.title}")
        except Exception as e:
            print(f"\nError during API call: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Configuration Fields in `ApiSettings`

*   `pre_request_hooks` (list of callables):
    *   Description: A list of functions to be called before each request.
    *   Default: `[]` (empty list)
*   `post_request_hooks` (list of callables):
    *   Description: A list of functions to be called after each response is received and processed.
    *   Default: `[]` (empty list)

These settings are typically configured programmatically as shown above, as they involve passing actual function objects.

## Use Cases

*   **Detailed Logging:** Log request URLs, methods, headers, bodies, and response statuses, headers, and content for debugging or auditing.
*   **Metrics Collection:** Gather data on request timings, success/failure rates, or API usage patterns.
*   **Request Modification:**
    *   Dynamically add or modify request headers (e.g., for tracing, custom authentication tokens not handled by built-in auth).
    *   Modify query parameters (use with caution, as this might interfere with client logic).
*   **Response Enrichment/Validation:**
    *   Perform custom validation on response data beyond Pydantic's capabilities.
    *   Trigger events or notifications based on specific response content (e.g., if a certain field in the response meets a condition).
*   **Debugging:** Print out intermediate states or data during the request-response flow.

## Important Considerations

*   **Performance:** Hooks are executed synchronously within the async request flow. Keep hook functions lightweight and efficient to avoid significantly impacting performance. Avoid blocking I/O operations within hooks if possible, or ensure they are also async if the hook system supports async callables (check library specifics if needed, though typical hooks are sync).
*   **Error Handling in Hooks:** Errors raised within a hook function will propagate and could potentially disrupt the request or response processing. Implement robust error handling within your hook functions if necessary.
*   **Order of Execution:** Hooks are executed in the order they appear in the list.
*   **Idempotency (for modifying hooks):** If your pre-request hooks modify the request, be mindful of idempotency if retries occur. The hook will be called again for each retry attempt.

The hook system in AIREloom provides a powerful way to extend and customize client behavior to fit specific application needs.
