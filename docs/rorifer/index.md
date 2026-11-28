# rorifer

rorifer is not yet published on PyPI. Until the first release, use it from a checkout of the `bibliofabric` workspace, where `uv sync --all-packages` installs it together with the `bibliofabric` 0.8 it needs.

rorifer is a Python client for the [ROR API v2](https://ror.readme.io/docs/rest-api), built on [bibliofabric](https://github.com/utsmok/bibliofabric). It types the organizations endpoint with Pydantic models, serializes the ROR filter syntax for you, and reads the registry dumps that ROR publishes on Zenodo. It ships an async client and a generated sync twin with the same API. The API needs no credentials.

## Install

```bash
uv sync --all-packages
```

The command runs in a checkout of the `bibliofabric` workspace and installs rorifer with the `bibliofabric` 0.8 it needs. `uv add rorifer` works once the package is on PyPI. Requires Python 3.12 or newer.

## Quick start

```python
import asyncio
from rorifer import RoriferClient


async def main():
    async with RoriferClient() as client:
        org = await client.organizations.get("006hf6230")
        print(org.display_name, org.status)

        page = await client.organizations.search(query="university of twente")
        print(page.total, [org.display_name for org in page.results])

        chosen = [
            match.organization
            for match in await client.organizations.match_affiliation(
                "University of Twente, Enschede, Netherlands"
            )
            if match.chosen
        ]
        print(chosen[0].id)


asyncio.run(main())
```

`client.organizations` exposes `get()`, `exists()`, `search()`, `iterate()`, `collect()`, `first()`, and `count()`, plus `match_affiliation()`, `find_by_external_id()`, and `find_by_funder_doi()`. `client.dumps` lists the registry dumps on Zenodo and downloads one.

## Sync usage

`RoriferSyncClient` is generated from the async source and behaves the same. The sync client uses plain `httpx.Client` and never starts or touches an event loop, so it works in scripts, in Jupyter, in threads, and when called from inside a running event loop.

```python
from rorifer import RoriferSyncClient

with RoriferSyncClient() as client:
    org = client.organizations.get("https://ror.org/006hf6230")
    print(org.display_name)

    for org in client.organizations.iterate(
        {"types": ["education", "nonprofit"], "country.country_code": "NL"}, limit=200
    ):
        print(org.id, org.established)
```

## Settings

`RoriferSettings` loads from environment variables prefixed with `RORIFER_` and from a `.env` file in the working directory. `RORIFER_MAX_REQUESTS_PER_SECOND` (default 6) and `RORIFER_MAX_CONCURRENCY` (default 5) set the request pace. Requests to Zenodo, which lists the data dumps, run in their own rate class: `RORIFER_RATE_LIMITS` is a JSON object of requests per second per class and defaults to `{"zenodo": 0.5}`, because the anonymous Zenodo search accepts 30 requests per minute. A `RORIFER_MAX_REQUESTS_PER_SECOND` that you set applies to every class, unless you also set `RORIFER_RATE_LIMITS`. The shared fields of `bibliofabric.config.BaseApiSettings` also apply, such as `RORIFER_TIMEOUT`, `RORIFER_MAX_RETRIES`, `RORIFER_MAX_RETRY_WAIT`, and `RORIFER_USER_AGENT`.

## Where to go next

- [Organizations](organizations.md) covers records, search, filters, affiliation matching, and the identifier lookup.
- [Data dumps](dumps.md) covers the Zenodo dumps and how to read all 150,000 records.
- [Upstream quirks](upstream-quirks.md) lists what the live API does differently from its documentation.
- The [API reference](reference.md) is generated from the source.
