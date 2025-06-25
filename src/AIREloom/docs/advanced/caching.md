# Client-Side Caching

AIREloom offers an optional client-side caching mechanism to improve performance and reduce the number of redundant API calls, especially for frequently accessed and rarely changing data.

## Purpose of Caching

*   **Reduced Latency:** Subsequent requests for the same resource can be served directly from the local cache, resulting in faster response times.
*   **Lower API Usage:** By serving responses from cache, AIREloom reduces the load on the OpenAIRE API servers and helps stay within rate limits.
*   **Improved Application Performance:** Faster data retrieval can lead to a more responsive application.

## How It Works

When caching is enabled:

*   AIREloom uses an in-memory **LRU (Least Recently Used)** cache.
*   Only `GET` requests are typically considered for caching. Operations that modify data (like `POST`, `PUT`, `DELETE`) are not cached.
*   When a `GET` request is made:
    1.  AIREloom first checks if a valid (non-expired) response for the same URL and parameters exists in the cache.
    2.  If a valid cached response is found, it's returned immediately without making an API call.
    3.  If not found or if the cached entry has expired (exceeded its Time-To-Live, TTL), AIREloom makes the actual API request.
    4.  The successful response from the API is then stored in the cache for future use before being returned to your application.

## Configuration Settings

Caching behavior is controlled by the following settings in `aireloom.config.ApiSettings`. You can configure them via [environment variables or programmatically](../advanced/configuration.md).

*   `enable_caching` (bool):
    *   Description: Globally enables or disables the client-side caching feature.
    *   Environment Variable: `AIRELOOM_ENABLE_CACHING`
    *   Default: `False` (Caching is disabled by default)

*   `cache_ttl_seconds` (int):
    *   Description: The Time-To-Live for cache entries, in seconds. After this duration, a cached item is considered stale and will be re-fetched from the API upon the next request.
    *   Environment Variable: `AIRELOOM_CACHE_TTL_SECONDS`
    *   Default: `300` (5 minutes)

*   `cache_max_size` (int):
    *   Description: The maximum number of entries to store in the LRU cache. When the cache reaches this size, the least recently used items will be evicted to make space for new ones.
    *   Environment Variable: `AIRELOOM_CACHE_MAX_SIZE`
    *   Default: `128`

## Enabling and Configuring Caching

### Via Environment Variables or `.env` File

To enable caching with default TTL and size, set in your environment or `.env` file:

```dotenv
AIRELOOM_ENABLE_CACHING=true
```

To customize further:

```dotenv
AIRELOOM_ENABLE_CACHING=true
AIRELOOM_CACHE_TTL_SECONDS=600  # Cache entries for 10 minutes
AIRELOOM_CACHE_MAX_SIZE=256     # Store up to 256 items
```

### Programmatically

You can enable and configure caching by passing an `ApiSettings` instance when creating an `AireloomSession`:

```python
import asyncio
from aireloom import AireloomSession
from aireloom.config import ApiSettings
from bibliofabric.auth import NoAuth # Or your preferred auth strategy

async def main():
    custom_settings = ApiSettings(
        enable_caching=True,
        cache_ttl_seconds=900,  # 15 minutes
        cache_max_size=100
    )

    async with AireloomSession(settings=custom_settings, auth_strategy=NoAuth()) as session:
        # First call to an endpoint will fetch from API and cache
        print("Fetching product for the first time...")
        product1 = await session.research_products.get("openaire____::doi:10.5281/zenodo.7664304")
        print(f"Fetched: {product1.title}")

        # Subsequent call for the same resource (within TTL) should be served from cache
        print("\nFetching product for the second time...")
        product2 = await session.research_products.get("openaire____::doi:10.5281/zenodo.7664304")
        print(f"Fetched (likely from cache): {product2.title}")

        # Verify if it's the same instance (simple check, real caching is more complex)
        # Note: Pydantic models might create new instances even if data is from cache.
        # The key is that no HTTP request is made if served from cache.
        # Logging within the HTTP client would confirm this.

if __name__ == "__main__":
    asyncio.run(main())
```

## Benefits and Considerations

### Benefits:
*   **Speed:** Significantly faster responses for repeated requests to the same resources.
*   **Efficiency:** Reduces the number of calls to the OpenAIRE API, saving bandwidth and respecting API usage quotas.

### Considerations:
*   **Data Freshness (Staleness):** Cached data might become stale if the underlying resource changes on the server before the cache TTL expires. Choose a TTL value that balances performance gains with the need for data freshness. For rapidly changing data, a shorter TTL or disabling caching for specific calls might be necessary.
*   **Memory Usage:** The cache is stored in memory. While the `cache_max_size` limits its growth, be mindful of memory constraints in resource-limited environments if you set a very large cache size.
*   **Cache Scope:** The cache is typically per `AireloomClient` instance (and thus per `AireloomSession` unless a custom client is shared). If you create multiple independent sessions, they will have separate caches.

Caching is a powerful tool for optimizing interactions with APIs. Configure it thoughtfully based on your application's requirements and data access patterns.
