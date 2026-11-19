# Exceptions

All exceptions derive from `BibliofabricError` and carry the `request` and
`response` of the failed call when available. `APIError` and its subclasses
also carry `body`, the parsed JSON error payload (or `None`), so callers can
read fields like OpenAlex's `reason`.

```
BibliofabricError
├── ConfigurationError
├── AuthError                 # 401/403, token fetch failure
├── NetworkError              # DNS failure, connection refused
├── TimeoutError              # also a builtin TimeoutError
├── ValidationError           # response record failed pydantic validation
└── APIError                  # other error statuses
    ├── NotFoundError         # 404
    └── RateLimitError        # 429
```

`ValidationError` carries `raw` (the rejected payload), `error` (the pydantic
exception), and `model_name`. `get()` and `search()` raise it; `iterate()`
raises it by default and drops bad records with `on_error="skip"`, collecting
them in `failures`.

Error strings redact credential query parameters such as `api_key` and token
values from URLs.

## API reference

::: bibliofabric.exceptions
    options:
      show_root_heading: true
