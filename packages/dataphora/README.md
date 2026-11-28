# dataphora: Python client for the DataCite REST API (async and sync)

Samuel Mok -- 2026

dataphora is a Python client for the
[DataCite REST API](https://support.datacite.org/docs/rest-api), built on
[bibliofabric](https://github.com/utsmok/bibliofabric). It types the public
read routes for DOIs, clients, providers, repositories, prefixes, prefix
assignments, activities, and events with Pydantic models, flattens the
JSON:API envelope so record fields sit at the top level, and sends queries
to the public GraphQL API. The async client is the source of truth; a
generated sync twin (`DataphoraSyncClient`, `DoisSyncClient`) offers the
same API without an event loop. Public reads need no login.

**Docs:** [utsmok.github.io/bibliofabric/dataphora](https://utsmok.github.io/bibliofabric/dataphora/) -- **License:** MIT

## Features

- **Async and sync**: built on `httpx`; the generated sync twin has the same
  API.
- **Typed records**: every resource model exposes `id`, all attributes, and
  the JSON:API `relationships` at the top level; unknown fields are kept as
  extras.
- **All query power**: `query=`, the full filter set (`client-id`,
  `prefix`, `resource-type-id`, `state`, and friends), sort options, sparse
  fieldsets (`fields[dois]`), and cursor paging beyond the 10,000-record
  numbered-paging limit.
- **Polite by default**: paced at 1.5 requests per second, under the
  documented anonymous budget of 500 requests per 5 minutes.

## Installation

```bash
uv sync --all-packages
```

The package is not yet published on PyPI. The command runs in a checkout of the `bibliofabric` workspace and installs dataphora with the `bibliofabric` 0.8 it needs. `uv add dataphora` works once the package is on PyPI. Requires Python >=3.12.

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
clients add `totals()` for the DOI production statistics and a `dois()` helper
that reads the DOIs of one account or prefix.

### Sync quick start

```python
from dataphora import DataphoraSyncClient

with DataphoraSyncClient() as client:
    doi = client.dois.get("10.5438/0012")
    print(doi.title, doi.publicationYear)

    for client_record in client.clients.search(query="zenodo", limit=5):
        print(client_record.symbol, client_record.name)
```

## Settings

`DataphoraSettings` loads from environment variables prefixed with
`DATAPHORA_`: `DATAPHORA_MAX_REQUESTS_PER_SECOND` (default 1.5),
`DATAPHORA_MAX_CONCURRENCY` (default 3), `DATAPHORA_TIMEOUT`,
`DATAPHORA_MAX_RETRIES`, `DATAPHORA_MAX_RETRY_WAIT`,
`DATAPHORA_USER_AGENT`, and `DATAPHORA_MAILTO`. Public reads need no
credentials, and the client never sends any.

## Upstream behavior to know

- **Unknown query parameters are silently ignored.** A misspelled filter
  returns an unfiltered result instead of an error; prefer the typed filter
  models.
- **Anonymous reads only see `findable` records.** The `registered` and
  `draft` states need a login.
- **Cursor paging always walks in `created` ascending order**, whatever
  `sort` says. Numbered paging can reach the first 10,000 records of a query
  only.
- **`/events` is slow without a filter.** Pass at least one filter (for
  example `doi=`) when you search events.

See [upstream quirks](../dataphora/upstream-quirks.md) for the full list
and for the routes that need a login.
