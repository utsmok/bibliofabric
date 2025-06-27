# Bibliofabric

Bibliofabric is a foundational Python library designed to provide a generic, robust, and extensible framework for building asynchronous API clients, particularly for scholarly and bibliometric data sources.

## Overview

The primary goal of Bibliofabric is to abstract away common complexities involved in interacting with web APIs, such as:

- Asynchronous HTTP requests using `httpx`.
- Automatic retries with exponential backoff for transient errors.
- Client-side caching for GET requests.
- Rate limit detection and handling.
- Pluggable authentication strategies.
- Consistent error handling and logging.
- API-agnostic response parsing through a protocol-based approach (`ResponseUnwrapper`).

Bibliofabric is intended to be used as a core dependency for specific API client libraries (like `aireloom` for OpenAIRE), rather than being used directly by end-users for typical data retrieval tasks. It provides the building blocks that enable rapid development of consistent and modern API clients.

## Core Features

- **Async-first:** Built from the ground up using `asyncio` and `httpx` for high-performance, non-blocking I/O.
- **Type-Safe:** Fully type-hinted to leverage static analysis for bug prevention and improved developer experience.
- **Extensible:** Designed with protocols and base classes that make it easy to add support for new APIs.
- **Configurable:** Settings for retries, timeouts, caching, and more can be managed via Pydantic settings models (environment variables or `.env` files).
- **Modular:** Clear separation between generic client infrastructure and API-specific logic.

## Intended Usage

Bibliofabric provides the `BaseApiClient`, `BaseApiSettings`, and various resource mixins (`GettableMixin`, `SearchableMixin`, `CursorIterableMixin`) that specific clients (like `aireloom`) inherit from and specialize.

Developers building a new API client would typically:
1. Define Pydantic models for the target API's data structures.
2. Create a `ResponseUnwrapper` implementation for the API's specific JSON response format.
3. Implement an authentication strategy if needed (or use provided ones).
4. Subclass `BaseApiClient` and/or `BaseResourceClient` and mixins to create clients for specific API endpoints.

## Installation (as a local dependency)

In the context of the current project structure, `bibliofabric` is typically installed as a local, editable dependency by other packages within the same monorepo or workspace (e.g., `aireloom`).

Example in a `pyproject.toml` of a dependent package:
```toml
[project]
# ...
dependencies = [
    "bibliofabric @ {root:uri}/../bibliofabric",
    # other dependencies...
]
```

This setup allows for simultaneous development of `bibliofabric` and the libraries that consume it.
