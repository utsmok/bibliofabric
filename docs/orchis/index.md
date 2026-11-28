# orchis

orchis is not yet published on PyPI; until its first release it installs from the bibliofabric workspace.

orchis is a Python client for the [ORCID Public API v3.0](https://info.orcid.org/documentation/integration-guide/public-api/), built on [bibliofabric](https://github.com/utsmok/bibliofabric). It types the record, person, activities, and search endpoints with Pydantic models and ships an async client with a generated sync twin. The public API answers reads without credentials.

The upstream references for this package are the [Public API guide](https://info.orcid.org/documentation/integration-guide/public-api/) and the [swagger document](https://pub.orcid.org/v3.0/) it links to. Facts in these pages were verified against the live API on 2026-11-27; see [upstream quirks](upstream-quirks.md).

## Install

```bash
uv add orchis
```

Requires Python 3.12 or newer.

## Pages

- [Records](records.md): the record summary and its XML representation.
- [Person](person.md): the person section and its sub-sections.
- [Activities](activities.md): the summary, the twelve sections, and single items.
- [Search](search.md): expanded search and the Solr-compatible route.
- [Upstream quirks](upstream-quirks.md): verified behavior that differs from what you might expect.
- [API reference](reference.md): generated from the source.

## Quick start

```python
import asyncio
from orchis import OrchisClient


async def main():
    async with OrchisClient() as client:
        record = await client.record.get("0000-0002-1694-233X")
        print(record.person.name.given_names.text)
        page = await client.expanded_search.search(
            query="family-name:Kucsko", page_size=10
        )
        print(page.total, [(r.given_names, r.family_names) for r in page.results])


asyncio.run(main())
```

## Sync usage

The generated `OrchisSyncClient` has the same methods without `async` and `await`:

```python
from orchis import OrchisSyncClient

with OrchisSyncClient() as client:
    work = client.activities.work("0000-0002-1694-233X", 145464015)
    print(work.title.title.text)
```

## Settings

`OrchisSettings` loads from environment variables prefixed with `ORCHIS_` and from a `.env` file in the working directory. The shared fields of `bibliofabric.config.BaseApiSettings` apply, such as `ORCHIS_MAX_CONCURRENCY`, `ORCHIS_TIMEOUT`, `ORCHIS_MAX_RETRIES`, and `ORCHIS_USER_AGENT`.

## Rate limits

ORCID documents 12 requests per second for anonymous and public API callers and 24 for the member API, with a burst of 40. The client defaults to 4 requests per second; raise it with `ORCHIS_MAX_REQUESTS_PER_SECOND`.

## Credentials

A token lifts the daily read quota from 25,000 to 100,000 reads for a registered public API client. Give the client one of two things:

- `ORCHIS_ACCESS_TOKEN`: a token you already hold. The client sends it as a bearer header.
- `ORCHIS_CLIENT_ID` and `ORCHIS_CLIENT_SECRET`: the credentials of your public API client. The client mints a `/read-public` token at `https://orcid.org/oauth/token` on the first request, reuses it, and mints a new one after a 401.

`ORCHIS_ACCESS_TOKEN` wins when both are set. Setting only one of the client id and secret raises `ConfigurationError`.

```python
settings = OrchisSettings(client_id="APP-XXXXXXXXXXXXXXXX", client_secret="...")
async with OrchisClient(settings=settings) as client:
    record = await client.record.get("0000-0002-1694-233X")
```
