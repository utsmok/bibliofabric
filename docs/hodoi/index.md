# hodoi

The package is not yet published on PyPI. Until the first release, install it from a checkout of the `bibliofabric` workspace, where `uv sync --all-packages` installs it together with the `bibliofabric` 0.8 it needs.

hodoi is a Python client for the DOI System proxy server at [doi.org](https://www.doi.org), built on [bibliofabric](https://github.com/utsmok/bibliofabric). It looks up the registration agency of a DOI, reads the Handle.net record behind it, returns the redirect a DOI resolves to, and retrieves metadata through content negotiation in every representation Crossref, DataCite, and mEDRA serve. It ships an async client and a generated sync twin with the same API. The proxy needs no credentials.

## Install

```bash
uv sync --all-packages
```

Run the command from the root of the `bibliofabric` workspace checkout. It requires Python 3.12 or newer.

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

`HodoiSettings` loads from environment variables prefixed with `HODOI_` and from a `.env` file in the working directory. `HODOI_MAX_REQUESTS_PER_SECOND` (default 2) and `HODOI_MAX_CONCURRENCY` (default 2) set the request pace, `HODOI_TIMEOUT` (default 60) sets the timeout, and `HODOI_FOLLOW_REDIRECTS` (default off) decides whether a request follows the resolver's 302. doi.org publishes no rate limit, so the pace is a courtesy. The other shared fields of `bibliofabric.config.BaseApiSettings` also apply, such as `HODOI_MAX_RETRIES`, `HODOI_MAX_RETRY_WAIT`, and `HODOI_USER_AGENT`.

## Where to go next

- [Registration agencies](agencies.md) covers the `/ra/` lookup, single and batched.
- [Handles](handles.md) covers the handle records, the landing URLs, the redirect of a DOI, and its redirect targets.
- [Metadata](metadata.md) covers content negotiation and its media types.
- The [API reference](reference.md) is generated from the source, and [upstream quirks](upstream-quirks.md) lists what the live service does, verified on 2026-11-27 and 2026-11-28.
