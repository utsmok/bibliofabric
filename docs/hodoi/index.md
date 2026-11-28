# hodoi

hodoi is a placeholder name. The package will be renamed before its first release.

hodoi is a Python client for the DOI System proxy server at [doi.org](https://www.doi.org), built on [bibliofabric](https://github.com/utsmok/bibliofabric). It resolves which registration agency holds a DOI, reads the Handle.net record behind it, and retrieves metadata through content negotiation in every representation Crossref, DataCite, and mEDRA serve. It ships an async client and a generated sync twin with the same API. The proxy needs no credentials.

## Install

```bash
uv add hodoi
```

Requires Python 3.12 or newer.

## Quick start

```python
import asyncio
from hodoi import CSL_JSON, HodoiClient


async def main():
    async with HodoiClient() as client:
        print(await client.agency("10.1038/nature12373"))
        item = await client.content("10.1038/nature12373", CSL_JSON)
        print(item.title)
        print(await client.landing_url("10.1038/nature12373"))


asyncio.run(main())
```

## Sync usage

The generated `HodoiSyncClient` has the same methods without `async` and `await`:

```python
from hodoi import CSL_JSON, HodoiSyncClient

with HodoiSyncClient() as client:
    record = client.handle("10.1038/nature12373")
    item = client.content("10.1038/nature12373", CSL_JSON)
    print(item.title)
```

## Settings

`HodoiSettings` loads from environment variables prefixed with `HODOI_` and from a `.env` file in the working directory. `HODOI_MAX_REQUESTS_PER_SECOND` (default 2) and `HODOI_MAX_CONCURRENCY` (default 2) set the request pace, and `HODOI_TIMEOUT` (default 60) sets the timeout. doi.org publishes no rate limit, so the pace is a courtesy. The other shared fields of `bibliofabric.config.BaseApiSettings` also apply, such as `HODOI_MAX_RETRIES`, `HODOI_MAX_RETRY_WAIT`, and `HODOI_USER_AGENT`.

## Where to go next

- [Registration agencies](agencies.md) covers the `/ra/` lookup, single and batched.
- [Handles](handles.md) covers the `/api/handles/` records and landing URLs.
- [Metadata](metadata.md) covers content negotiation and its media types.
- [Upstream quirks](upstream-quirks.md) lists what the live service actually does, verified on 2026-11-27.
- The [API reference](reference.md) is generated from the source.
