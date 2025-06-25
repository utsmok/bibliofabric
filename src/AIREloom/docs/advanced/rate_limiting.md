# Rate Limiting

AIREloom includes features to help your application respect API rate limits imposed by OpenAIRE services. This is crucial for maintaining fair usage and preventing your access from being temporarily blocked.

## How AIREloom Handles Rate Limits

When `enable_rate_limiting` is active (which it is by default), AIREloom's internal HTTP client inspects response headers for standard rate limit information and reacts accordingly.

### Key HTTP Headers

AIREloom looks for the following common rate limit headers in API responses:

*   `X-RateLimit-Limit`: The total number of requests allowed in the current window.
*   `X-RateLimit-Remaining`: The number of requests remaining in the current window.
*   `X-RateLimit-Reset`: The time (often in UTC epoch seconds or a relative number of seconds) when the current rate limit window resets.
*   `Retry-After`: Sent with a `429 Too Many Requests` status code, indicating how many seconds your application should wait before retrying.

### Behavior

1.  **Proactive Pausing (Buffer):**
    *   If `X-RateLimit-Remaining` is present and falls below a certain threshold (calculated using `rate_limit_buffer_percentage`), AIREloom may proactively pause before sending the next request. This helps to avoid exhausting the quota too quickly.
    *   The pause duration might be estimated based on `X-RateLimit-Reset` if available, or a short, fixed duration.
    *   *Note: The exact implementation of proactive pausing can vary and might be refined in future versions.*

2.  **Handling `429 Too Many Requests`:**
    *   If the API returns a `429` status code, AIREloom will:
        *   Check for a `Retry-After` header. If present, it will wait for the specified number of seconds before attempting a retry.
        *   If `Retry-After` is not present, it will wait for `rate_limit_retry_after_default` seconds.
        *   The request will be retried up to `max_retries` times, with exponential backoff applied in conjunction with the `Retry-After` delay.

3.  **Retry Mechanism:**
    *   The general retry mechanism (controlled by `max_retries` and `backoff_factor`) also applies to `429` errors, working alongside the specific rate limit delays.

## Configuration Settings

These settings, found in `aireloom.config.ApiSettings`, control the rate limiting behavior. You can configure them via [environment variables or programmatically](../advanced/configuration.md).

*   `enable_rate_limiting` (bool):
    *   Description: Globally enables or disables all built-in rate limiting features. If set to `False`, AIREloom will not inspect rate limit headers or automatically handle `429` errors by waiting (though retries for other server errors might still occur based on `max_retries`).
    *   Environment Variable: `AIRELOOM_ENABLE_RATE_LIMITING`
    *   Default: `True`

*   `rate_limit_buffer_percentage` (float):
    *   Description: A safety buffer. For example, if `0.1` (10%) and `X-RateLimit-Limit` is 100, AIREloom might consider pausing or slowing down when `X-RateLimit-Remaining` drops below 10. This is more of a heuristic for future enhancements in proactive pausing.
    *   Environment Variable: `AIRELOOM_RATE_LIMIT_BUFFER_PERCENTAGE`
    *   Default: `0.1`

*   `rate_limit_retry_after_default` (int):
    *   Description: The default number of seconds to wait if a `429` response is received without a `Retry-After` header.
    *   Environment Variable: `AIRELOOM_RATE_LIMIT_RETRY_AFTER_DEFAULT`
    *   Default: `60`

*   `max_retries` (int):
    *   Description: The maximum number of times a request will be retried if it fails due to a `429` error (or other retryable errors).
    *   Environment Variable: `AIRELOOM_MAX_RETRIES`
    *   Default: `3`

## Example Scenario

Consider the following sequence:

1.  You make several requests, and `X-RateLimit-Remaining` is decreasing.
2.  If `X-RateLimit-Remaining` becomes very low (factoring in `rate_limit_buffer_percentage`), the client *might* introduce a small delay before the next request (this behavior is more conceptual for current version but planned for more robust handling).
3.  You make a request that exceeds your quota. The API returns a `429 Too Many Requests` status.
    *   **Case A:** The response includes `Retry-After: 120` (wait 120 seconds).
        *   AIREloom will pause for 120 seconds.
        *   After the pause, it will retry the request (if `max_retries` has not been exhausted).
    *   **Case B:** The response does *not* include a `Retry-After` header.
        *   AIREloom will pause for `rate_limit_retry_after_default` seconds (e.g., 60 seconds).
        *   After the pause, it will retry.
4.  If retries also result in `429` and `max_retries` is reached, a `RateLimitError` (a subclass of `APIError`) will be raised.

## Best Practices

*   **Always enable rate limiting:** Keep `enable_rate_limiting = True` unless you have a very specific reason to disable it and are handling rate limits externally.
*   **Be mindful of batch operations:** If you are sending many requests in a loop (e.g., using `iterate()` or making many `get()` calls), be aware that rate limits can still be hit. The client will attempt to handle them, but very aggressive request patterns might lead to longer overall processing times due to enforced waits.
*   **Check API Documentation:** Refer to the specific OpenAIRE API documentation for details on their rate limiting policies, as these can vary between endpoints or based on your authentication level.
*   **Adjust `max_retries` and `backoff_factor`:** If you find that default retry settings are too aggressive or not persistent enough for your use case, adjust them in your configuration.

By understanding and utilizing AIREloom's rate limiting features, you can build more robust and considerate applications that interact smoothly with OpenAIRE services.
