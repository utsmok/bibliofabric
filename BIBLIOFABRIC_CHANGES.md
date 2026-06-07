# Bibliofabric Enhancement Plan: Multi-API Compatibility

> **Goal**: Make bibliofabric's parameter handling configurable so downstream libraries (syntheca/OpenAlex, future libraries) can customize query param names, filter serialization, and auth — without duplicating mixin logic.

> **Constraint**: Every change defaults to current behavior. Zero impact on AIREloom.

---

## Change 1: Configurable Query Parameter Names

### Problem
`SearchableMixin`, `CursorIterableMixin`, `PageIterableMixin`, and `GettableMixin` hardcode parameter names (`page`, `pageSize`, `sortBy`, `cursor`). OpenAlex uses different names (`page`, `per_page`, `sort`, `cursor`).

### File: `src/bibliofabric/resources.py`

### 1a. Add class attributes to `BaseResourceClient` (after line 70)

```python
class BaseResourceClient:
    # ... existing ...
    _base_url_override: str | None = None
    _supports_direct_get: bool = False

    # NEW: Configurable query parameter names.
    # Override in subclasses to match the target API's parameter naming.
    _param_page: str = "page"
    _param_page_size: str = "pageSize"
    _param_sort: str = "sortBy"
    _param_cursor: str = "cursor"
    _param_id: str = "id"
```

### 1b. Update `SearchableMixin.search()` (lines 366-370)

Replace hardcoded strings:
```python
# BEFORE:
params["page"] = page
params["pageSize"] = page_size
if sort_by:
    self._validate_sort_field(sort_by.split()[0])
    params["sortBy"] = sort_by

# AFTER:
params[self._param_page] = page
params[self._param_page_size] = page_size
if sort_by:
    self._validate_sort_field(sort_by.split()[0])
    params[self._param_sort] = sort_by
```

### 1c. Update `CursorIterableMixin.iterate()` (lines 473-481, 535, 537)

```python
# BEFORE (line 473-481):
current_params: dict[str, Any] = {
    "cursor": "*",
    "pageSize": page_size,
}
if sort_by:
    current_params["sortBy"] = sort_by

# AFTER:
current_params: dict[str, Any] = {
    self._param_cursor: "*",
    self._param_page_size: page_size,
}
if sort_by:
    self._validate_sort_field(sort_by.split()[0])
    current_params[self._param_sort] = sort_by

# BEFORE (line 535):
current_params["cursor"] = next_cursor
current_params.pop("page", None)

# AFTER:
current_params[self._param_cursor] = next_cursor
current_params.pop(self._param_page, None)
```

### 1d. Update `PageIterableMixin.iterate()` (lines 604-617)

```python
# BEFORE:
if sort_by:
    self._validate_sort_field(sort_by.split()[0])
    params["sortBy"] = sort_by
...
    params["page"] = current_page
    params["pageSize"] = page_size

# AFTER:
if sort_by:
    self._validate_sort_field(sort_by.split()[0])
    params[self._param_sort] = sort_by
...
    params[self._param_page] = current_page
    params[self._param_page_size] = page_size
```

### 1e. Update `GettableMixin.get()` non-direct path (line 265)

```python
# BEFORE:
params = {"id": entity_id, "pageSize": 1}

# AFTER:
params = {self._param_id: entity_id, self._param_page_size: 1}
```

### 1f. Update `ResourceClientProtocol` (add after line 46)

```python
class ResourceClientProtocol(Protocol):
    # ... existing ...
    _param_page: str
    _param_page_size: str
    _param_sort: str
    _param_cursor: str
    _param_id: str
```

### Backward compatibility
All defaults match current hardcoded values. AIREloom inherits defaults — no change needed.

### Tests needed in `tests/test_resources.py`
- Verify `SearchableTestClient` still sends `page`, `pageSize`, `sortBy` with defaults
- Create `OpenAlexStyleClient(BaseResourceClient, SearchableMixin)` with overridden params → verify sends `page`, `per_page`, `sort`
- Same for `CursorIterableMixin` and `PageIterableMixin` with custom param names
- Verify `GettableMixin.get()` non-direct path uses custom `_param_id` and `_param_page_size`

---

## Change 2: Pluggable Filter Serialization

### Problem
Bibliofabric serializes filter models as individual query params (`model_dump()` → spread into `params`). OpenAlex needs a single `filter` param with structured syntax (`field:value,field:value`).

### File: `src/bibliofabric/resources.py`

### 2a. Add method to `BaseResourceClient` (after `_validate_sort_field`)

```python
def _serialize_filters(
    self, filters: BaseModel | dict[str, Any] | None
) -> dict[str, Any]:
    """Convert filter criteria to query parameters.

    Override in subclasses for custom filter serialization.
    Default behavior: dump Pydantic model to dict (or copy dict),
    producing individual query parameters per field.

    Returns:
        dict[str, Any]: Query parameters representing the filters.
    """
    if filters is None:
        return {}
    if isinstance(filters, BaseModel):
        return filters.model_dump(exclude_none=True, by_alias=True)
    if isinstance(filters, dict):
        return dict(filters)
    raise BibliofabricError(
        f"filters must be a Pydantic model or dictionary, got {type(filters)}"
    )
```

### 2b. Replace inline filter serialization in all 3 mixins

**`SearchableMixin.search()`** (lines 355-365):
```python
# BEFORE:
params: dict[str, Any] = {}
if filters:
    if isinstance(filters, BaseModel):
        params = filters.model_dump(exclude_none=True, by_alias=True)
    elif isinstance(filters, dict):
        params = dict(filters)
    else:
        raise BibliofabricError(...)

# AFTER:
params = self._serialize_filters(filters)
```

**`CursorIterableMixin.iterate()`** (lines 455-465):
```python
# BEFORE:
filter_dict: dict[str, Any] = {}
if filters:
    if isinstance(filters, BaseModel):
        filter_dict = filters.model_dump(exclude_none=True, by_alias=True)
    elif isinstance(filters, dict):
        filter_dict = filters
    else:
        raise BibliofabricError(...)

# AFTER:
filter_dict = self._serialize_filters(filters)
```

**`PageIterableMixin.iterate()`** (lines 591-601):
```python
# BEFORE:
params: dict[str, Any] = {}
if filters:
    if isinstance(filters, BaseModel):
        params = filters.model_dump(exclude_none=True, by_alias=True)
    elif isinstance(filters, dict):
        params = dict(filters)
    else:
        raise BibliofabricError(...)

# AFTER:
params = self._serialize_filters(filters)
```

### Backward compatibility
Default `_serialize_filters()` does exactly what the inline code does today. AIREloom inherits default — no change.

### Tests needed
- Verify default `_serialize_filters()` produces same output as current inline code
- Create subclass that overrides `_serialize_filters()` to produce OpenAlex-style `filter` string
- Verify `SearchableMixin`, `CursorIterableMixin`, `PageIterableMixin` all call `_serialize_filters()`

---

## Change 3: Optional `search` Parameter on Mixins

### Problem
OpenAlex has a top-level `search=<query>` query parameter for full-text search. Bibliofabric's mixins don't accept this. Currently the only way to pass it is through the filters dict, which is semantically wrong.

### File: `src/bibliofabric/resources.py`

### 3a. Add class attribute to `BaseResourceClient`

```python
_param_search: str = "search"  # Set to None to disable search param
```

### 3b. Add `search` parameter to `SearchableMixin.search()`

```python
async def search(
    self: ResourceClientProtocol,
    page: int = 1,
    page_size: int = 20,
    sort_by: str | None = None,
    filters: BaseModel | dict[str, Any] | None = None,
    search: str | None = None,  # NEW
) -> BaseModel | dict[str, Any]:
```

Add after filter serialization:
```python
if search is not None and self._param_search:
    params[self._param_search] = search
```

### 3c. Add `search` parameter to `CursorIterableMixin.iterate()`

```python
async def iterate(
    self: ResourceClientProtocol,
    page_size: int = 100,
    sort_by: str | None = None,
    filters: BaseModel | dict[str, Any] | None = None,
    search: str | None = None,  # NEW
) -> AsyncIterator[Any]:
```

Add after filter dict merge:
```python
if search is not None and self._param_search:
    current_params[self._param_search] = search
```

### 3d. Add `search` parameter to `PageIterableMixin.iterate()`

Same pattern as 3c.

### 3e. Update `BaseResourceClient.collect()` and `count()`

Add `search: str | None = None` parameter to both methods, pass through to `iterate()`/`search()`.

### Backward compatibility
`search=None` by default. Existing callers don't pass it — no change.

### Tests needed
- Verify `search` param is added to query when provided
- Verify it's omitted when `None` (default)
- Verify AIREloom-style clients work without passing `search`

---

## Change 4: QueryParameterAuth Strategy

### Problem
OpenAlex authenticates via `?api_key=XXX` as a query parameter. Bibliofabric's `AuthStrategy` only mutates request headers.

### File: `src/bibliofabric/auth.py`

### 4a. Add `QueryParameterAuth` class (after `StaticTokenAuth`)

```python
class QueryParameterAuth:
    """Auth strategy that injects credentials as a URL query parameter.

    Some APIs (e.g., OpenAlex) authenticate by requiring a specific query
    parameter (like ``api_key``) on every request. This strategy appends
    the parameter to the request URL.

    Args:
        key_name: The query parameter name (e.g., ``"api_key"``).
        key_value: The credential value.
    """

    def __init__(self, key_name: str, key_value: str):
        self._key_name = key_name
        self._key_value = key_value

    async def async_authenticate(self, request: httpx.Request) -> None:
        """Append the API key as a query parameter to the request URL."""
        request.url = request.url.copy_merge_params(
            {self._key_name: self._key_value}
        )
        logger.trace(
            f"QueryParameterAuth: appended '{self._key_name}' to request URL."
        )

    async def async_close(self) -> None:
        """No resources to close for QueryParameterAuth."""
```

### 4b. Update `AuthStrategyType` enum

```python
class AuthStrategyType(Enum):
    NONE = "none"
    STATIC_TOKEN = "static_token"
    CLIENT_CREDENTIALS = "client_credentials"
    QUERY_PARAMETER = "query_parameter"  # NEW
```

### 4c. Update `__init__.py` exports

Add `QueryParameterAuth` to imports and `__all__`.

### Backward compatibility
New class. Existing strategies untouched. AIREloom doesn't use it.

### Tests needed in `tests/test_auth.py`
- Verify `async_authenticate` appends key to URL
- Verify existing request params are preserved
- Verify URL encoding of special characters
- Verify `async_close` is no-op

---

## Change 5: Update `ResourceClientProtocol`

### File: `src/bibliofabric/resources.py`

Add all new class attributes to the Protocol so type checkers recognize them on mixin `self` usage:

```python
class ResourceClientProtocol(Protocol):
    _api_client: "BaseApiClient"
    _entity_path: str
    _entity_model: type[BaseModel] | None
    _search_response_model: type[BaseModel] | None
    _base_url_override: str | None
    _supports_direct_get: bool

    # NEW (from Changes 1-3):
    _param_page: str
    _param_page_size: str
    _param_sort: str
    _param_cursor: str
    _param_id: str
    _param_search: str

    @property
    def response_unwrapper(self) -> "ResponseUnwrapper": ...
    def _validate_sort_field(self, field: str) -> None: ...
    def _serialize_filters(self, filters: BaseModel | dict[str, Any] | None) -> dict[str, Any]: ...
```

---

## Implementation Order

1. **Change 1** (param names) — straightforward attribute extraction, touches 4 mixins + protocol
2. **Change 5** (protocol update) — must accompany Change 1
3. **Change 2** (filter serialization) — extract method, replace 3 inline blocks
4. **Change 3** (search param) — additive, optional param on 3 mixins + collect/count
5. **Change 4** (QueryParameterAuth) — independent, new file section + exports

All can be done in a single branch. Each change should be its own commit for clean review.

---

## AIREloom Verification

After all changes, run AIREloom's full test suite against the updated bibliofabric:

```bash
cd ~/dev/AIREloom
uv sync --all-groups  # picks up local bibliofabric
uv run pytest tests/ --cov=aireloom
```

Expected: all tests pass, no behavioral changes.

---

## Summary of Touched Files

| File | Changes |
|------|---------|
| `src/bibliofabric/resources.py` | Class attributes on `BaseResourceClient`, `_serialize_filters()` method, param name variables in 4 mixins + protocol update, `search` param on 3 mixins + collect/count |
| `src/bibliofabric/auth.py` | `QueryParameterAuth` class, `AuthStrategyType` enum entry |
| `src/bibliofabric/__init__.py` | Export `QueryParameterAuth` |
| `tests/test_resources.py` | New tests for param name overrides, filter serialization override, search param |
| `tests/test_auth.py` | New tests for `QueryParameterAuth` |
