# dataphora

dataphora is a Python client for the
[DataCite REST API](https://support.datacite.org/docs/rest-api), built on
[bibliofabric](https://github.com/utsmok/bibliofabric). It types the public
read routes for DOIs, clients, providers, repositories, prefixes, prefix
assignments, activities, and events, flattens the JSON:API envelope so
record fields sit at the top level of each model, and sends queries to the
public GraphQL API. It ships an async client and a generated sync twin with
the same API. The name is a placeholder and will change before the first
release.

## Install

The package is not yet on PyPI. Until the rename lands, install from the
monorepo and import it with `PYTHONPATH=packages/dataphora/src`.

Requires Python 3.12 or newer.

## Authentication

Public reads need no login and no key. The client never sends credentials.
Routes that need a login (DOI writes, media, usage reports, draft and
registered records, API keys) are not wrapped; see
[upstream quirks](upstream-quirks.md).

Anonymous traffic is metered at 500 requests per 5 minutes. The client
paces itself at 1.5 requests per second by default.

## Quick start

```python
import asyncio
from dataphora import DataphoraClient


async def main():
    async with DataphoraClient() as client:
        doi = await client.dois.get("10.5438/0012")
        print(doi.title, doi.resource_type, doi.client_id)

        page = await client.dois.search(
            {"client-id": "cern.zenodo", "resource-type-id": "dataset"},
            query="photosynthesis",
            select=["doi", "titles"],
        )
        print(page.total, len(page.results))

        async for record in client.dois.iterate({"prefix": "10.5438"}, limit=10):
            print(record.doi, record.created)


asyncio.run(main())
```

Every resource client exposes `get()`, `exists()`, `search()`, `iterate()`,
`collect()`, `first()`, and `count()`. The clients, providers, and prefixes
clients add `totals()` for DOI production statistics and a `dois()` helper
that reads the DOIs of one account or prefix. Start with the
[DOIs](usage/dois.md) page.

## Sync usage

`DataphoraSyncClient` is generated from the async source and behaves the
same: same parameters, errors, retries, paging, and rate limits. It uses
plain `httpx.Client` and never starts or touches an event loop.

```python
from dataphora import DataphoraSyncClient

with DataphoraSyncClient() as client:
    doi = client.dois.get("10.5438/0012")
    print(doi.title, doi.publicationYear)

    for record in client.providers.search(page_size=5):
        print(record.symbol, record.displayName)
```

## Settings

`DataphoraSettings` loads from environment variables prefixed with
`DATAPHORA_`: `DATAPHORA_MAX_REQUESTS_PER_SECOND` (default 1.5),
`DATAPHORA_MAX_CONCURRENCY` (default 3), `DATAPHORA_TIMEOUT` (default
30), `DATAPHORA_MAX_RETRIES` (default 3), `DATAPHORA_MAX_RETRY_WAIT`,
`DATAPHORA_USER_AGENT`, and `DATAPHORA_MAILTO`.

## Where to go next

- One usage page per resource family: [dois](usage/dois.md),
  [clients](usage/clients.md), [providers](usage/providers.md),
  [repositories](usage/repositories.md), [prefixes](usage/prefixes.md),
  [events](usage/events.md), [media](usage/media.md), and
  [GraphQL](usage/graphql.md).
- [Upstream quirks](upstream-quirks.md) observed in the live DataCite API.
- The [API reference](reference.md) is generated from the source.
