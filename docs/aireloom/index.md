# AIREloom

AIREloom is an async Python client for the OpenAIRE Graph API and the
Scholexplorer API. It is built on the shared
[bibliofabric](https://github.com/utsmok/bibliofabric) core, which provides
retries, rate limiting, and pagination; AIREloom adds the OpenAIRE query
dialect, typed filter models, and response parsing.

## Install

```bash
uv add aireloom
```

Python 3.12 or later is required.

## Quick start

```python
import asyncio

from aireloom import AireloomClient


async def main() -> None:
    async with AireloomClient() as client:
        page = await client.research_products.search(query="quantum dots", page_size=10)
        for product in page.results:
            print(product.id, product.mainTitle)


asyncio.run(main())
```

Without credentials the client is anonymous. For the registered-service
quota, set `AIRELOOM_OPENAIRE_CLIENT_ID` and
`AIRELOOM_OPENAIRE_CLIENT_SECRET` (environment variables or a `.env` file);
the client then fetches a bearer token from the OpenAIRE Keycloak endpoint
and reuses it until it expires.

## Sync usage

AIREloom ships two variants of every client class. The async code is the
single source of truth; the sync twins are generated from it with
[unasync](https://github.com/python-unasync/unasync) and committed.

| Async | Sync |
|---|---|
| `AireloomClient` | `AireloomSyncClient` |
| `ResearchProductsResource` | `SyncResearchProductsResource` |
| `ScholixResource` | `SyncScholixResource` |

Use the async client inside `asyncio` applications. Use the sync client in
scripts and notebooks, or from code that runs inside a running event loop:
it uses `httpx.Client`, `time.sleep`, and threads, and never starts or
touches an event loop.

```python
from aireloom import AireloomSyncClient

with AireloomSyncClient() as client:
    page = client.research_products.search(query="quantum dots", page_size=10)
    for product in page.results:
        print(product.id, product.mainTitle)
```

Both variants take the same parameters, raise the same errors, retry and
page the same way, and enforce the same rate limits. Every resource
attribute of `AireloomSyncClient` (`research_products`, `projects`,
`organizations`, `data_sources`, `persons`, `scholix`) exposes the matching
`Sync*` resource class.

## The client

| Attribute | Resource | Host |
|---|---|---|
| `client.research_products` | V4 research products plus link helpers | Graph |
| `client.projects` | V4 projects | Graph |
| `client.organizations` | V4 organizations | Graph |
| `client.data_sources` | V4 data sources | Graph |
| `client.persons` | V4 persons | Graph |
| `client.research_products.search_links` | V3 relations between products | Graph |
| `client.scholix` | Scholexplorer `Links` (V3, V2 for dates) | Scholexplorer |

Every entity resource supports `search`, `iterate`, `collect`, `first`,
`count`, `facets`, and `group_by`. `get(id)` reads the V3 by-id route
because V4 has none. See the usage pages for each resource family.

## Documentation

- [Research products](usage/research_products.md)
- [Projects, organizations, data sources, persons](usage/projects.md)
- [Links](usage/links.md) and [Scholix](usage/scholix.md)
- [Errors, retries, and rate limits](errors.md)
- [Upstream quirks](quirks.md)
- [API reference](api.md)
