# Stavrophora

Stavrophora is a Python client for the [Crossref REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/), with an async variant and a generated sync twin. It is built on [bibliofabric](https://github.com/utsmok/bibliofabric) and covers the works, journals, funders, members, types, prefixes, and licenses routes with typed Pydantic models.

## Install

Requires Python 3.12 or newer.

```bash
uv add stavrophora
```

## Quick start

```python
import asyncio

from stavrophora import StavrophoraClient


async def main() -> None:
    async with StavrophoraClient(mailto="you@example.org") as client:
        work = await client.works.get("10.1038/nature12373")
        print(work.primary_title)

        page = await client.works.search(
            query="proteomics", select=["DOI", "title"], page_size=5
        )
        for work in page.results:
            print(work.doi, work.primary_title)


asyncio.run(main())
```

`search()` returns a `Page` with `.results` (typed models), `.total`, `.next_cursor`, and `.meta` (the response envelope minus the results).

## Sync usage

Every class has a generated sync twin: `StavrophoraClient` pairs with `StavrophoraSyncClient`, and each resource class pairs with a `Sync`-prefixed twin (`WorksResource` -> `SyncWorksResource`). Both variants take the same parameters, raise the same errors, retry and page the same way, and enforce the same per-class rate limits.

```python
from stavrophora import StavrophoraSyncClient

with StavrophoraSyncClient(mailto="you@example.org") as client:
    work = client.works.get("10.1038/nature12373")
    page = client.works.search(query="proteomics", select=["DOI", "title"], page_size=5)
    for work in page.results:
        print(work.doi, work.primary_title)
```

The sync client uses `httpx.Client`, `time.sleep`, and threads, and never starts or touches an event loop, so it works in plain scripts, in Jupyter, and when called from inside a running event loop. See [Sync usage](../bibliofabric/sync.md) for when to pick which variant.

## Credentials

The Crossref API needs no authentication. Two optional credentials change how requests are sent:

| Credential | How to set it | What it does |
|---|---|---|
| Polite pool email | `mailto=` or `STAVROPHORA_MAILTO` | Sent as a `mailto` query parameter; raises your rate limits |
| Metadata Plus key | `plus_token=` or `STAVROPHORA_PLUS_TOKEN` | Sent as a `crossref-api-key: Bearer <key>` header |

A `plus_token` replaces `mailto` as the credential when both are set. An explicit `auth_strategy=` argument overrides both.

## Where to go next

- [Works](works.md): search, filters, cursor iteration, batch DOI lookup, facets, sample, agency, and scoped works routes.
- [Errors, retries, rate limits](errors.md).
- [Crossref quirks](quirks.md): behavior the client defends against.
- [API reference](reference.md).
