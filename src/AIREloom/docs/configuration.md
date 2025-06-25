# Configuration

AIREloom's behavior can be configured through environment variables or by passing parameters directly when instantiating `AireloomSession` or `ApiSettings`. Environment variables are prefixed with `AIRELOOM_`.

The settings are managed by the `ApiSettings` class in `aireloom.config`.

## Client Behavior Settings

These settings control the general behavior of the HTTP client.

*   **`AIRELOOM_REQUEST_TIMEOUT`**
    *   Description: Default request timeout in seconds.
    *   Default: `30.0`
    *   Example: `export AIRELOOM_REQUEST_TIMEOUT="60"`

*   **`AIRELOOM_MAX_RETRIES`**
    *   Description: Maximum number of retries for failed requests.
    *   Default: `3`
    *   Example: `export AIRELOOM_MAX_RETRIES="5"`

*   **`AIRELOOM_BACKOFF_FACTOR`**
    *   Description: Backoff factor for retries (seconds). This determines how long to wait before retrying a failed request. The wait time typically increases with each retry.
    *   Default: `0.5`
    *   Example: `export AIRELOOM_BACKOFF_FACTOR="1.0"`

*   **`AIRELOOM_USER_AGENT`**
    *   Description: User-Agent header for requests. It's good practice to set a custom User-Agent that identifies your application.
    *   Default: (A default AIREloom User-Agent, e.g., `aireloom-python-client/0.1.0`)
    *   Example: `export AIRELOOM_USER_AGENT="MyResearchApp/1.0 (contact@example.com)"`

## Rate Limiting Settings

These settings control how AIREloom handles API rate limits.

*   **`AIRELOOM_ENABLE_RATE_LIMITING`**
    *   Description: Enable/disable API rate limiting features. If enabled, the client will try to respect `Retry-After` headers and manage request rates.
    *   Default: `True`
    *   Example: `export AIRELOOM_ENABLE_RATE_LIMITING="false"`

*   **`AIRELOOM_RATE_LIMIT_BUFFER_PERCENTAGE`**
    *   Description: Buffer percentage to consider rate limit approaching (e.g., 0.1 for 10%). This can be used by more advanced rate limiting strategies to slow down before hitting actual limits.
    *   Default: `0.1`
    *   Example: `export AIRELOOM_RATE_LIMIT_BUFFER_PERCENTAGE="0.2"`

*   **`AIRELOOM_RATE_LIMIT_RETRY_AFTER_DEFAULT`**
    *   Description: Default wait time in seconds if a `429 Too Many Requests` response is received without a `Retry-After` header.
    *   Default: `60`
    *   Example: `export AIRELOOM_RATE_LIMIT_RETRY_AFTER_DEFAULT="120"`

## Authentication Settings

These settings are used to configure authentication with OpenAIRE APIs. See the [Authentication](authentication.md) guide for more details on how these are used.

*   **`AIRELOOM_OPENAIRE_API_TOKEN`**
    *   Description: Static OpenAIRE API Token (optional). Used for `StaticTokenAuth`.
    *   Default: `None`
    *   Example: `export AIRELOOM_OPENAIRE_API_TOKEN="your_secret_token"`

*   **`AIRELOOM_OPENAIRE_CLIENT_ID`**
    *   Description: OpenAIRE Client ID for OAuth2 (required for `ClientCredentialsAuth`).
    *   Default: `None`
    *   Example: `export AIRELOOM_OPENAIRE_CLIENT_ID="your_client_id"`

*   **`AIRELOOM_OPENAIRE_CLIENT_SECRET`**
    *   Description: OpenAIRE Client Secret for OAuth2 (required for `ClientCredentialsAuth`).
    *   Default: `None`
    *   Example: `export AIRELOOM_OPENAIRE_CLIENT_SECRET="your_client_secret"`

*   **`AIRELOOM_OPENAIRE_TOKEN_URL`**
    *   Description: OAuth2 Token Endpoint URL. This is used by `ClientCredentialsAuth` to fetch an access token.
    *   Default: The OpenAIRE registered service API token URL (defined in constants.py as REGISTERED_SERVICE_API_TOKEN_URL)
    *   Example: `export AIRELOOM_OPENAIRE_TOKEN_URL="https://custom.openaire.token/url"`

## Programmatic Configuration

You can also configure AIREloom programmatically by creating an instance of `ApiSettings` and passing it to the `AireloomSession`:

```python
from aireloom import AireloomSession
from aireloom.config import ApiSettings, AuthStrategyType

custom_settings = ApiSettings(
    auth_strategy=AuthStrategyType.STATIC_TOKEN,
    api_token="your_secret_token_here",
    request_timeout=60.0,
    # ... other settings
)

async def main():
    async with AireloomSession(settings=custom_settings) as session:
        # Use the session configured with custom_settings
        # product = await session.research_products.get("some_id")
        pass
```
This method takes precedence over environment variables or `.env` files for the settings provided.
## Loading Settings

Settings are loaded by `pydantic-settings` from:
1.  Environment variables (prefixed with `AIRELOOM_`).
2.  A `.env` file in the current working directory.
3.  A `secrets.env` file in the current working directory.

Values provided directly during `AireloomSession` or `ApiSettings` instantiation will take precedence over environment variables or .env files.
