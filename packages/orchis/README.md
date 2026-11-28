# orchis

orchis is not yet published on PyPI; until its first release it installs from the bibliofabric workspace.

orchis is a Python client for the [ORCID Public API v3.0](https://info.orcid.org/documentation/integration-guide/public-api/), built on [bibliofabric](https://github.com/utsmok/bibliofabric). It types the record, person, activities, and search endpoints with Pydantic models, unwraps the `{"value": ...}` wrappers for you, and ships an async client with a generated sync twin. The public API answers reads without credentials.

## Install

```bash
uv add orchis
```

Requires Python 3.12 or newer.

## Quick start

```python
import asyncio
from orchis import OrchisClient


async def main():
    async with OrchisClient() as client:
        record = await client.record.get("0000-0002-1694-233X")
        print(record.person.name.given_names.text, record.person.name.family_name.text)

        works = await client.activities.works("0000-0002-1694-233X")
        print(works.put_codes()[:5])

        page = await client.expanded_search.search(
            query="family-name:Kucsko", page_size=10
        )
        print(page.total, [(r.given_names, r.family_names) for r in page.results])


asyncio.run(main())
```

`client.record` fetches the record summary; `client.person` covers the person section and its sub-sections; `client.activities` covers the activities summary, each section, and the single-item routes such as `client.activities.work(orcid, put_code)`; `client.expanded_search` and `client.search` cover the two search routes. Wrapped values answer their text through the `text` property (or the module-level `text()` helper), so you never walk `{"value": ...}` dictionaries.

## Sync usage

`OrchisSyncClient` is generated from the async source and behaves the same.

```python
from orchis import OrchisSyncClient

with OrchisSyncClient() as client:
    work = client.activities.work("0000-0002-1694-233X", 145464015)
    print(work.title.title.text, work.publication_date.iso())
```

## Settings

Settings load from the environment with the `ORCHIS_` prefix. The client defaults to 4 requests per second (ORCID allows 12 for anonymous and public API callers and 24 for the member API). A token lifts the daily read quota from 25,000 to 100,000 reads for a registered public API client: set `ORCHIS_ACCESS_TOKEN` to a token you hold, or set `ORCHIS_CLIENT_ID` and `ORCHIS_CLIENT_SECRET` and the client mints a `/read-public` token on the first request.

## License

MIT.
