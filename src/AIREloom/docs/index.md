# AIREloom Documentation

Welcome to the official documentation for AIREloom, an asynchronous Python client library designed to interact with the OpenAIRE Graph API and other OpenAIRE services. It provides a user-friendly interface for accessing research products, projects, organizations, data sources, and Scholix links.

## Key Features

*   **Asynchronous Operations:** Built with `httpx` and `asyncio` for non-blocking I/O, enabling efficient handling of concurrent API requests.
*   **Pydantic Models:** Ensures robust data validation, type hinting, and provides an intuitive way to work with API responses.
*   **Flexible Authentication:** Supports multiple strategies including No Authentication, Static API Token, and OAuth2 Client Credentials, with auto-detection from environment variables.
*   **Comprehensive API Coverage:** Clients for major OpenAIRE Graph API entities (Research Products, Projects, Organizations, Data Sources) and the Scholexplorer API (Scholix links).
*   **Efficient Data Retrieval:**
    *   Methods for fetching single entities by ID.
    *   Powerful `search()` methods with page-based pagination, filtering, and sorting capabilities.
    *   Convenient `iterate()` methods for automatically handling cursor-based pagination to retrieve all results matching a query.
*   **Resilience:** Built-in retry logic for transient network errors and common API error codes.
*   **Rate Limiting:** Configurable strategies to respect API rate limits and handle `429 Too Many Requests` errors gracefully. (See [Rate Limiting](advanced/rate_limiting.md))
*   **Caching:** Optional client-side caching for GET requests to improve performance and reduce API load. (See [Caching](advanced/caching.md))
*   **Extensible:** A basic hook system allows for injecting custom logic before requests are sent or after responses are received. (See [Request Hooks](advanced/hooks.md))
*   **Configurable:** Settings for timeouts, retries, base URLs, and more can be managed via environment variables, `.env` files, or direct instantiation. (See [Configuration](advanced/configuration.md))

## Table of Contents

*   **1. Overview**
    *   [README](../README.md) (Project overview, quick start, and core concepts)
*   **2. Getting Started**
    *   [Installation](installation.md)
    *   [Authentication](authentication.md)
    *   [Basic Usage Tutorial](getting_started.md)
*   **3. Usage Guides (By Resource)**
    *   [Research Products](usage/research_products.md)
    *   [Projects](usage/projects.md)
    *   [Organizations](usage/organizations.md)
    *   [Data Sources](usage/data_sources.md)
    *   [Scholix Links](usage/scholix.md)
*   **4. Advanced Topics**
    *   [Configuration](advanced/configuration.md)
    *   [Rate Limiting](advanced/rate_limiting.md)
    *   [Caching](advanced/caching.md)
    *   [Request Hooks](advanced/hooks.md)
    *   [Error Handling](advanced/error_handling.md)
*   **5. Contributing**
    *   [Contribution Guidelines](contributing.md)
*   **6. Project Information**
    *   [Changelog](changelog.md)
    *   [License](../LICENSE) (Link to root LICENSE file)

We hope this documentation helps you effectively use AIREloom to interact with OpenAIRE services.
