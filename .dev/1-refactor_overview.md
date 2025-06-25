# Refactor Overview: The `bibliofabric` Initiative

## 1. Vision

The ultimate goal is to create a comprehensive, modern, and maintainable Python toolkit for bibliometric and scholarly data retrieval. This toolkit will consist of multiple API client libraries (for OpenAIRE, Crossref, OpenAlex, etc.) and a high-level orchestration library that unifies them.

## 2. Problem Statement

The current `aireloom` library, while functional, is a monolithic implementation. It tightly couples generic HTTP client logic with OpenAIRE-specific details. Attempting to build clients for other APIs by copying and pasting this code would lead to:

-   **Code Duplication:** Logic for retries, caching, rate-limiting, and session management would be repeated in every library.
-   **Maintenance Overhead:** A bug fix or feature enhancement in the core client logic would need to be manually applied to every library.
-   **Inconsistent Developer Experience:** Subtle differences between libraries would inevitably emerge, making the final toolkit difficult for end-users to learn and use.

## 3. The Solution: `bibliofabric`

To address these challenges, we will refactor the existing `aireloom` codebase into two distinct packages:

1.  **`bibliofabric` (The Generic Framework):** A new, domain-agnostic library that will provide all the generic functionality required to build a modern asynchronous API client. Its responsibilities will include:
    -   A robust, `httpx`-based client with built-in retry logic, caching, and rate-limiting.
    -   A protocol-based authentication system (`AuthStrategy`).
    -   A generic exception hierarchy.
    -   Pluggable patterns for handling API-specific response structures and pagination (`ResponseUnwrapper`).
    -   Reusable base classes and mixins for common resource operations (`GettableMixin`, `IterableMixin`).

2.  **`aireloom` (The Specific Client):** The existing library, refactored to become a lightweight implementation that *uses* `bibliofabric`. Its responsibilities will be limited to:
    -   Defining OpenAIRE-specific Pydantic data models.
    -   Defining OpenAIRE-specific endpoint paths and filter models.
    -   Implementing the `ResponseUnwrapper` for the OpenAIRE API's specific JSON structure.
    -   Implementing any truly unique OpenAIRE API features (e.g., Scholix client logic).

## 4. Key Architectural Goals

-   **Decoupling:** Achieve a clean separation of concerns between generic client infrastructure and API-specific business logic.
-   **Maintainability:** Centralize core logic so that improvements and bug fixes benefit all libraries built on the framework.
-   **Extensibility:** Make it simple and fast to add new API clients to the toolkit by inheriting from `bibliofabric`.
-   **Developer Experience:** Ensure all future clients have a consistent and predictable interface for end-users.

## 5. Scope and Restrictions

-   This refactor is **strictly architectural**. It is not intended to add new features to the `aireloom` client itself.
-   The focus is on creating `bibliofabric` and refactoring `aireloom`. Prototyping a second client (e.g., for Crossref) is a validation step, not a primary goal of this initial phase.
-   The high-level orchestration library is out of scope for this phase.

## 6. Success Criteria

The refactor will be considered successful when:
1.  `bibliofabric` exists as a standalone, installable Python package.
2.  The `aireloom` package has a dependency on `bibliofabric`.
3.  The refactored `aireloom` client passes its entire original test suite (`verification_script.py`), proving no loss of functionality.
4.  The source code for `aireloom`'s resource clients (`ResearchProductsClient`, etc.) is significantly smaller and more declarative, with most logic inherited from `bibliofabric`.
