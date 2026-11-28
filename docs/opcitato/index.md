# opcitato

opcitato is a placeholder name. The package will be renamed before its first release.

opcitato is a Python client for the [OpenCitations Index API v2](https://opencitations.net/index/api/v2) and the [OpenCitations Meta API v1](https://opencitations.net/meta/api/v1), built on [bibliofabric](https://github.com/utsmok/bibliofabric). It types the citation rows and the bibliographic metadata with Pydantic models, parses the multi-identifier strings into `(scheme, value)` pairs, validates the prefixed identifiers before a request is sent, and reads the CSV representation into the same models. It ships an async client and a generated sync twin with the same API. The APIs need no credentials.

## Install

```bash
uv add opcitato
```

Requires Python 3.12 or newer.

## Quick start

```python
import asyncio
from opcitato import OpcitatoClient


async def main():
    async with OpcitatoClient() as client:
        citations = await client.index.citations("doi:10.1108/jd-12-2013-0166")
        print(len(citations), citations[0].oci)

        count = await client.index.citation_count("doi:10.1108/jd-12-2013-0166")
        print("incoming citations:", count)

        records = await client.meta.metadata("doi:10.1007/978-1-4020-9632-7")
        print(records[0].title, records[0].pub_date)


asyncio.run(main())
```

`client.index` exposes the six Index operations (`citation()`, `citations()`, `references()`, `citation_count()`, `reference_count()`, `venue_citation_count()`). `client.meta` exposes the three Meta operations (`metadata()`, `author()`, `editor()`). Every operation answers with the complete result; neither API pages.

## Sync usage

`OpcitatoSyncClient` is generated from the async source and behaves the same. The sync client uses plain `httpx.Client` and never starts or touches an event loop, so it works in scripts, in Jupyter, in threads, and when called from inside a running event loop.

```python
from opcitato import OpcitatoSyncClient

with OpcitatoSyncClient() as client:
    for record in client.meta.author("orcid:0000-0002-8420-0696"):
        print(record.pub_date, record.title)
```

## Settings

`OpcitatoSettings` loads from environment variables prefixed with `OPCITATO_` and from a `.env` file in the working directory. `OPCITATO_MAX_REQUESTS_PER_SECOND` (default 3, matching the documented limit of 180 requests per minute per IP address) and `OPCITATO_MAX_CONCURRENCY` (default 3) set the request pace. The shared fields of `bibliofabric.config.BaseApiSettings` also apply, such as `OPCITATO_TIMEOUT`, `OPCITATO_MAX_RETRIES`, `OPCITATO_MAX_RETRY_WAIT`, and `OPCITATO_USER_AGENT`.

## Where to go next

- [Index API](index-api.md) covers citations, references, counts, and the row-shaping parameters.
- [Meta API](meta-api.md) covers metadata, authors, editors, and multi-id requests.
- [Upstream quirks](upstream-quirks.md) lists what the live APIs do differently from their documentation, with the dates each fact was verified.
- The [API reference](reference.md) is generated from the source.
