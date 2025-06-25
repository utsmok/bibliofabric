# Authentication

AIREloom supports several authentication strategies for interacting with OpenAIRE APIs. The client can automatically detect the appropriate strategy based on your environment configuration, or you can explicitly provide one.

## Automatic Detection

By default, when you initialize an `AireloomSession` without an explicit `auth_strategy`, AIREloom will attempt to configure authentication in the following order of preference:

1.  **OAuth2 Client Credentials:** If `AIRELOOM_OPENAIRE_CLIENT_ID` and `AIRELOOM_OPENAIRE_CLIENT_SECRET` environment variables (or corresponding settings in your `.env` file) are found.
2.  **Static API Token:** If `AIRELOOM_OPENAIRE_API_TOKEN` is found.
3.  **No Authentication:** If neither of the above is configured.

## Configuration Methods

You can provide credentials and settings for authentication through:

*   Environment Variables
*   A `.env` file (or `secrets.env`) in your project root
*   Directly passing parameters when instantiating an authentication strategy class.

### Environment Variables / `.env` File

Create a `.env` or `secrets.env` file in your project root. AIREloom will automatically load these variables. Ensure your environment variables are prefixed with `AIRELOOM_`.

#### 1. Static API Token

Set the `AIRELOOM_OPENAIRE_API_TOKEN` variable:

```dotenv
AIRELOOM_OPENAIRE_API_TOKEN="your_static_api_token_here"
```

This token will be used in the `Authorization` header for API requests.

#### 2. OAuth2 Client Credentials

Set the following variables:

*   `AIRELOOM_OPENAIRE_CLIENT_ID`: Your OAuth2 client ID.
*   `AIRELOOM_OPENAIRE_CLIENT_SECRET`: Your OAuth2 client secret.
*   `AIRELOOM_OPENAIRE_TOKEN_URL` (Optional): The URL to fetch the OAuth2 token. If not provided, it defaults to the standard OpenAIRE token URL (`https://services.openaire.eu/uoa-oauth2-common/oauth2/token`).

```dotenv
AIRELOOM_OPENAIRE_CLIENT_ID="your_client_id_here"
AIRELOOM_OPENAIRE_CLIENT_SECRET="your_client_secret_here"
# AIRELOOM_OPENAIRE_TOKEN_URL="https://custom.token.url/oauth/token" # Optional override
```

AIREloom will automatically request an access token using these credentials and manage its refresh.

## Explicit Authentication Strategies

You can explicitly define the authentication strategy when creating an `AireloomSession` by passing an instance of an authentication class from `bibliofabric.auth`.

### 1. No Authentication (`NoAuth`)

For APIs or endpoints that do not require authentication.

```python
from aireloom import AireloomSession
from bibliofabric.auth import NoAuth

async with AireloomSession(auth_strategy=NoAuth()) as session:
    # API calls will be made without any Authorization header
    pass
```

### 2. Static API Token (`StaticTokenAuth`)

Uses a pre-obtained static API token.

```python
from aireloom import AireloomSession
from bibliofabric.auth import StaticTokenAuth

# Token can be provided directly
auth_strategy = StaticTokenAuth(token="your_actual_api_token")

# Or, if AIRELOOM_OPENAIRE_API_TOKEN is set in the environment,
# it will be used if 'token' parameter is None (or not provided):
# auth_strategy = StaticTokenAuth()

async with AireloomSession(auth_strategy=auth_strategy) as session:
    # API calls will use "Authorization: Bearer your_actual_api_token"
    pass
```
If `token` is not provided to `StaticTokenAuth()`, it will attempt to load it from the `AIRELOOM_OPENAIRE_API_TOKEN` environment variable.

### 3. OAuth2 Client Credentials (`ClientCredentialsAuth`)

Manages fetching and refreshing OAuth2 access tokens using the client credentials flow.

```python
from aireloom import AireloomSession
from bibliofabric.auth import ClientCredentialsAuth

# Credentials can be provided directly:
# auth_strategy = ClientCredentialsAuth(
#     client_id="your_client_id",
#     client_secret="your_client_secret",
#     token_url="https://your.custom.token/url" # Optional, defaults to OpenAIRE's
# )

# Or, they will be read from environment variables if parameters are None or not provided:
# (AIRELOOM_OPENAIRE_CLIENT_ID, AIRELOOM_OPENAIRE_CLIENT_SECRET, AIRELOOM_OPENAIRE_TOKEN_URL)
auth_strategy = ClientCredentialsAuth()

async with AireloomSession(auth_strategy=auth_strategy) as session:
    # AIREloom will handle token acquisition and refresh
    pass
```
If `client_id`, `client_secret`, or `token_url` are not provided to `ClientCredentialsAuth()`, they will be sourced from their respective `AIRELOOM_` prefixed environment variables.

## Default Behavior Example

This example demonstrates how `AireloomSession` initializes with the default authentication detection mechanism.

```python
import asyncio
from aireloom import AireloomSession

# Assuming environment variables are set for Client Credentials or Static Token,
# or neither for NoAuth.
#
# Order of detection:
# 1. ClientCredentialsAuth (if AIRELOOM_OPENAIRE_CLIENT_ID & AIRELOOM_OPENAIRE_CLIENT_SECRET are set)
# 2. StaticTokenAuth (if AIRELOOM_OPENAIRE_API_TOKEN is set)
# 3. NoAuth (if neither of the above)

async def main():
    async with AireloomSession() as session: # No explicit auth_strategy
        # The session will be configured with the auto-detected strategy.
        print(f"Session initialized with auth strategy: {type(session._client._auth_strategy).__name__}")
        # Example: try to fetch a protected or public resource
        try:
            # Replace with an actual API call relevant to your auth level
            # For example, fetching a research product (often public)
            product = await session.research_products.get("openaire____::doi:10.5281/zenodo.7664304") # Example ID
            print(f"Successfully fetched: {product.title}")
        except Exception as e:
            print(f"Error during API call: {e}")

if __name__ == "__main__":
    # To test, configure your .env file or environment variables accordingly
    # e.g., for Client Credentials:
    # AIRELOOM_OPENAIRE_CLIENT_ID="your_id"
    # AIRELOOM_OPENAIRE_CLIENT_SECRET="your_secret"
    asyncio.run(main())
```

Choose the authentication method that best suits your needs and the requirements of the OpenAIRE API endpoints you are accessing. For more details on obtaining API tokens or client credentials, please refer to the official OpenAIRE documentation.
