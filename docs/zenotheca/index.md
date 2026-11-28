# zenotheca

zenotheca is a placeholder name. The package will be renamed before its first release.

zenotheca is a Python client for the [Zenodo REST API](https://developers.zenodo.org/), built on [bibliofabric](https://github.com/utsmok/bibliofabric). It types the records, communities, and vocabularies endpoints with Pydantic models, wraps the OAI-PMH endpoint, builds the Elasticsearch `q` clauses for you, and streams file downloads to disk. It ships an async client and a generated sync twin with the same API.

## Install

```bash
uv add zenotheca
```

Requires Python 3.12 or newer.

## Authentication

Public reads need no token. With the optional `ZENOTHECA_API_TOKEN` set
the client sends `Authorization: Bearer` on every request and raises the
page size cap from 25 to 100, as documented upstream. Some routes outside
this client's scope (the legacy deposit routes, for example) need an
account and answer 403 without one.

## Quick start

```python
import asyncio
from zenotheca import ZenothecaClient, community, resource_type


async def main():
    async with ZenothecaClient() as client:
        record = await client.records.get("10.5281/zenodo.24378467")
        print(record.title, record.metadata.version)

        page = await client.records.search(
            {"type": "dataset"},
            query=community("ror-data"),
            sort="mostrecent",
        )
        print(page.total, [record.title for record in page.results])

        versions = await client.records.versions(record.id, page_size=5)
        print(versions.total)


asyncio.run(main())
```

`client.records` exposes `get()`, `exists()`, `search()`, `iterate()`,
`collect()`, `first()`, `count()`, `versions()`, `latest()`, `files()`, and
`download_file()`. `client.communities` exposes `search()`, `get()`,
`iterate()`, `records()`, and `subcommunities()`. `client.vocabularies`
exposes `search()`, `iterate()`, and `get()`. `client.oai` exposes the six
OAI-PMH verbs plus `iterate_records()` and `iterate_identifiers()`. Start
with [records](usage/records.md), [communities](usage/communities.md),
[vocabularies](usage/vocabularies.md), and [OAI-PMH](usage/oai.md).

## Sync usage

`ZenothecaSyncClient` is generated from the async source and behaves the
same. The sync client uses plain `httpx.Client` and never starts or touches
an event loop, so it works in scripts, in Jupyter, in threads, and when
called from inside a running event loop.

```python
from zenotheca import ZenothecaSyncClient

with ZenothecaSyncClient() as client:
    record = client.records.get(24378467)
    print(record.title)

    for record in client.communities.records("ror-data", {"type": "dataset"}, limit=3):
        print(record.id, record.title)
```

Use the async client in asyncio applications and for many concurrent
requests. Use the sync client everywhere else. Both read the `ZENOTHECA_*`
settings the same way.

## Settings

`ZenothecaSettings` loads from environment variables prefixed with
`ZENOTHECA_`: `ZENOTHECA_MAX_REQUESTS_PER_SECOND` (default 2),
`ZENOTHECA_MAX_CONCURRENCY` (default 5), `ZENOTHECA_TIMEOUT`,
`ZENOTHECA_MAX_RETRIES`, `ZENOTHECA_MAX_RETRY_WAIT`, and
`ZENOTHECA_USER_AGENT`, and `ZENOTHECA_API_TOKEN`. Zenodo publishes no
documented rate limit; the default keeps the client at a courtesy pace of
2 requests per second. Zenodo rejects requests without a `User-Agent`
header, and the client always sends one.

## Where to go next

- One usage page per resource family: [records](usage/records.md),
  [communities](usage/communities.md), [vocabularies](usage/vocabularies.md),
  and [OAI-PMH](usage/oai.md).
- [Upstream quirks](upstream-quirks.md) observed in the live Zenodo API.
- The [API reference](reference.md) is generated from the source.
