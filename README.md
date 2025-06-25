# `bibliofabric`: a foundation for modern scholarly API clients

`bibliofabric` is a foundational, asynchronous Python framework for building modern, resilient, and maintainable clients for scholarly APIs. It is the generic engine designed to create a future toolkit of clients for services like OpenAIRE, Crossref, OpenAlex, and more.

---

## Key Features

*   Built on `httpx` and `asyncio` for high-performance, non-blocking I/O.
*   Automatic retries for transient network errors and 5xx/429 status codes with configurable exponential backoff.
*   Supports various authentication schemes.
*   The `ResponseUnwrapper` can be adapted to all response structures.
*   Optional in-memory TTL caching for GET requests to reduce latency and API load.
*   Handles `429` errors by respecting `Retry-After` headers.
*   Inject custom logic before a request is sent or after a response is received with a hook system.

## Who is this for?

`bibliofabric` is a framework for developers building API clients. It is not an end-user library. You would use `bibliofabric` to create a library like `AIREloom`, which can then be used by researchers, librarians, data scientists, ....

## How to Build a Client with `bibliofabric` (Conceptual Example)

Here’s a simplified example of how you would build a client for a hypothetical "SimpleAPI".
The developer only needs to define the API-specific parts; the underlying boilerplay & logic is handled by `bibliofabric`.

```python
# simpleapi_client/client.py
from bibliofabric.client import BaseApiClient
from bibliofabric.config import BaseApiSettings
from bibliofabric.models import ResponseUnwrapper
from bibliofabric.resources import GettableMixin, BaseResourceClient
from pydantic import BaseModel

# 1. Define the API's data model
class SimpleWork(BaseModel):
    id: str
    title: str

# 2. Implement the ResponseUnwrapper for this specific API
class SimpleApiUnwrapper(ResponseUnwrapper[dict]):
    def unwrap_results(self, response_json: dict) -> list[dict]:
        return response_json.get("data", [])

    def unwrap_single_item(self, response_json: dict) -> dict:
        return response_json.get("item", {})

    # ... implement other protocol methods ...

# 3. Define the Resource Client using BiblioFabric's mixins
class WorksClient(GettableMixin, BaseResourceClient):
    _entity_path: str = "works"
    _entity_model: type[SimpleWork] = SimpleWork

# 4. Create the main client class
class SimpleApiClient(BaseApiClient):
    def __init__(self, settings: BaseApiSettings | None = None, auth_strategy=None):
        # Instantiate the unwrapper and pass it to the base client
        unwrapper = SimpleApiUnwrapper()
        super().__init__(
            base_url="https://api.simple.org/v1",
            settings=settings,
            auth_strategy=auth_strategy,
            response_unwrapper=unwrapper
        )
        # Attach the specific resource client
        self.works = WorksClient(api_client=self)

# 5. The end-user can now use your new client
async def main():
    async with SimpleApiClient() as client:
        work = await client.works.get("123")
        print(work.title)
```



### Core Architectural Concepts

`bibliofabric` is built on a few key, decoupled concepts:

*  The heart of the framework  is formed by the `BaseApiClient`. A robust, `httpx`-based asynchronous client that manages the entire request/response lifecycle, including retries, caching, rate limiting, and a hook system.
*   A pluggable system for authentication using `AuthStrategy`. Implementations for No-Auth, Static Bearer Token, and OAuth2 Client Credentials are provided out of the box, and adding new strategies (e.g., for Crossref's "polite pool") is straightforward.
*   `ResponseUnwrapper`: The key to flexibility. This protocol allows specific clients to teach the `BaseApiClient` how to navigate different API response "envelopes" (e.g., finding results in `response['results']` vs. `response['message']['items']`).
*   A set of pre-built mixins (`GettableMixin`, `SearchableMixin`, `CursorIterableMixin`) that provide the boilerplate logic for common REST operations (`.get()`, `.search()`, `.iterate()`), making specific client implementations incredibly lean and declarative.


# Contributing
Contributions are welcome! This project adheres to standard open-source practices. Please see our development guidelines for information on setting up your environment, coding conventions, and testing.

# License
This project is licensed under the MIT License.
