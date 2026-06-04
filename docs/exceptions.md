# Exceptions

bibliofabric defines a structured exception hierarchy rooted at `BibliofabricError`. All exceptions carry optional `httpx.Response` and `httpx.Request` context for debugging.

## Hierarchy

```
BibliofabricError              # Base — carries message, response, request
├── APIError                   # Non-specific 4xx/5xx
│   ├── NotFoundError          # 404
│   └── RateLimitError         # 429
├── ValidationError            # Invalid parameters / 400
├── TimeoutError               # Request timeout
├── NetworkError               # DNS failure, connection refused, etc.
├── ConfigurationError         # Misconfigured settings
├── AuthError                  # Token fetch failure, invalid credentials
└── BibliofabricRequestError   # General request-level errors
```

## API Reference

::: bibliofabric.exceptions
    options:
      show_source: false
      show_root_heading: true
