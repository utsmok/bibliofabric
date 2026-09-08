# Resources

The resources module provides composable mixins and a base class for building per-endpoint resource clients. Instead of writing boilerplate HTTP logic for each endpoint, you compose the right mixins and set a few class attributes.

## Building Blocks

| Component | Purpose |
|---|---|
| `ResourceClientProtocol` | Protocol defining the interface mixins expect (`_api_client`, `_entity_path`, `response_unwrapper`, etc.) |
| `BaseResourceClient` | Base class holding the API client reference and providing the `response_unwrapper` property |
| `GettableMixin` | Adds `get(entity_id)` — fetch a single entity by ID |
| `SearchableMixin` | Adds `search(params)` — paginated search returning typed results |
| `CursorIterableMixin` | Adds `iterate(params)` — async iterator using cursor-based pagination |
| `PageIterableMixin` | Adds `iterate(params)` — async iterator using page-based pagination |

## Quick Example

```python
from bibliofabric.resources import GettableMixin, SearchableMixin, BaseResourceClient

class WorksClient(
    GettableMixin,
    SearchableMixin,
    BaseResourceClient,
):
    _entity_path = "works"
    _entity_model = WorkModel          # Pydantic model for single entity
    _search_response_model = None      # Optional search envelope model
```

Mixins are designed to be composed — inherit the ones you need.

When model validation fails, resource `get()`, `search()`, and `iterate()` calls
keep their existing fallback behavior and accept an `on_validation_error` callback.
The callback receives a `ValidationErrorContext` with the rejected record or raw
response body and the validation exception. Use `raw=True` with `get()` or
`search()` when the HTTP response should be returned without parsing.

## API Reference

::: bibliofabric.resources
    options:
      show_source: false
      show_root_heading: true
