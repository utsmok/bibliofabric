# Configuration

AIREloom offers a flexible configuration system, primarily managed through the `ApiSettings` class, which loads values from environment variables or `.env` files. You can also override settings programmatically.

## Configuration Sources

Settings are loaded in the following order of precedence (highest first):

1.  **Directly passed `ApiSettings` instance:** When you initialize `AireloomClient` (or `AireloomSession` which uses it internally), you can pass your own `ApiSettings` object.
2.  **Environment Variables:** Variables prefixed with `AIRELOOM_` (e.g., `AIRELOOM_REQUEST_TIMEOUT`).
3.  **`.env` or `secrets.env` File:** Values defined in a `.env` or `secrets.env` file in your project root.
4.  **Default Values:** Predefined defaults in the `ApiSettings` class.

## Key Configurable Settings

All settings below can be configured by setting the corresponding environment variable (e.g., `AIRELOOM_REQUEST_TIMEOUT` for `request_timeout`) or by providing them when creating an `ApiSettings` instance.

### Client Behavior

*   `request_timeout` (float):
    *   Description: Default request timeout in seconds for API calls.
    *   Environment Variable: `AIRELOOM_REQUEST_TIMEOUT`
    *   Default: `30.0`
*   `max_retries` (int):
    *   Description: Maximum number of retries for failed requests due to transient network errors or specific HTTP status codes (like 5xx or 429 if rate limiting is enabled).
    *   Environment Variable: `AIRELOOM_MAX_RETRIES`
    *   Default: `3`
*   `backoff_factor` (float):
    *   Description: Backoff factor in seconds for calculating delays between retries. The delay is calculated as `backoff_factor * (2 ** (retry_attempt - 1))`.
    *   Environment Variable: `AIRELOOM_BACKOFF_FACTOR`
    *   Default: `0.5`
*   `user_agent` (str):
    *   Description: The User-Agent header string to be sent with requests.
    *   Environment Variable: `AIRELOOM_USER_AGENT`
    *   Default: `aireloom/{version}` (e.g., `aireloom/0.1.0`)

### API Base URLs

**Note:** Base URLs are currently hardcoded in `aireloom.endpoints` and are not configurable through `ApiSettings`. They are set as constants:

*   Graph API Base URL: `https://api.graph.openaire.eu/v1/` (defined in `aireloom.endpoints.GRAPH_API_BASE_URL`)
*   Scholexplorer API Base URL: `https://api-beta.scholexplorer.openaire.eu/v3/` (defined in `aireloom.endpoints.SCHOLIX_API_BASE_URL`)

These URLs are used internally by the client and cannot be overridden via environment variables or ApiSettings in the current version.

### Authentication

These settings are primarily for configuring authentication strategies. See the [Authentication Guide](../authentication.md) for more details.

*   `openaire_api_token` (str, optional):
    *   Description: Static OpenAIRE API Token.
    *   Environment Variable: `AIRELOOM_OPENAIRE_API_TOKEN`
    *   Default: `None`
*   `openaire_client_id` (str, optional):
    *   Description: OpenAIRE Client ID for OAuth2 client credentials flow.
    *   Environment Variable: `AIRELOOM_OPENAIRE_CLIENT_ID`
    *   Default: `None`
*   `openaire_client_secret` (str, optional):
    *   Description: OpenAIRE Client Secret for OAuth2 client credentials flow.
    *   Environment Variable: `AIRELOOM_OPENAIRE_CLIENT_SECRET`
    *   Default: `None`
*   `openaire_token_url` (str):
    *   Description: OAuth2 Token Endpoint URL.
    *   Environment Variable: `AIRELOOM_OPENAIRE_TOKEN_URL`
    *   Default: `https://aai.openaire.eu/oidc/token` (for registered services, from `aireloom.constants`)

### Rate Limiting

For details on how these settings are used, see the [Rate Limiting Guide](rate_limiting.md).

*   `enable_rate_limiting` (bool):
    *   Description: Enable or disable built-in API rate limiting features.
    *   Environment Variable: `AIRELOOM_ENABLE_RATE_LIMITING`
    *   Default: `True`
*   `rate_limit_buffer_percentage` (float):
    *   Description: A buffer (e.g., 0.1 for 10%) to consider the rate limit as approaching, potentially pausing before hitting the actual limit if `X-RateLimit-Remaining` is low.
    *   Environment Variable: `AIRELOOM_RATE_LIMIT_BUFFER_PERCENTAGE`
    *   Default: `0.1`
*   `rate_limit_retry_after_default` (int):
    *   Description: Default wait time in seconds if a `429 Too Many Requests` response is received without a `Retry-After` header.
    *   Environment Variable: `AIRELOOM_RATE_LIMIT_RETRY_AFTER_DEFAULT`
    *   Default: `60`

### Caching

For details on how these settings are used, see the [Caching Guide](caching.md).

*   `enable_caching` (bool):
    *   Description: Enable or disable client-side caching for GET requests.
    *   Environment Variable: `AIRELOOM_ENABLE_CACHING`
    *   Default: `False`
*   `cache_ttl_seconds` (int):
    *   Description: Default Time-To-Live for cache entries in seconds.
    *   Environment Variable: `AIRELOOM_CACHE_TTL_SECONDS`
    *   Default: `300` (5 minutes)
*   `cache_max_size` (int):
    *   Description: Maximum number of items to store in the LRU (Least Recently Used) cache.
    *   Environment Variable: `AIRELOOM_CACHE_MAX_SIZE`
    *   Default: `128`

### Hooks

These settings allow programmatic addition of hooks and are not typically set via environment variables. See the [Request Hooks Guide](hooks.md).

*   `pre_request_hooks` (list of callables):
    *   Description: List of hooks to call before a request is made.
    *   Default: `[]` (empty list)
*   `post_request_hooks` (list of callables):
    *   Description: List of hooks to call after a response is received and parsed.
    *   Default: `[]` (empty list)

## Using `.env` Files

Create a `.env` or `secrets.env` file in the root of your project:

```dotenv
# .env example
AIRELOOM_REQUEST_TIMEOUT=45.0
AIRELOOM_MAX_RETRIES=5
AIRELOOM_OPENAIRE_API_TOKEN="your_token_here"
AIRELOOM_ENABLE_CACHING=true
AIRELOOM_CACHE_TTL_SECONDS=600
```

AIREloom will automatically load these settings when `ApiSettings` is initialized.

## Programmatic Configuration

You can override any setting by creating an `ApiSettings` instance and passing it to `AireloomSession` or `AireloomClient`.

```python
import asyncio
from aireloom import AireloomSession
from aireloom.config import ApiSettings
from bibliofabric.auth import NoAuth

async def main():
    # Create custom settings
    custom_settings = ApiSettings(
        request_timeout=60.0,
        max_retries=2,
        enable_caching=True,
        cache_ttl_seconds=1800 # 30 minutes
    )

    # Initialize session with custom settings and an explicit auth strategy
    async with AireloomSession(settings=custom_settings, auth_strategy=NoAuth()) as session:
        # Your API calls here will use the custom_settings
        print(f"Session timeout: {session._client._http_client.timeout.read}")
        # ...
        pass

if __name__ == "__main__":
    asyncio.run(main())
```

This approach provides fine-grained control over the client's behavior for specific use cases or instances.
