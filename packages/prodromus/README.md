# prodromus

prodromus is not yet published on PyPI; until its first release it installs from the bibliofabric workspace.

prodromus is a Python client for the [bioRxiv and medRxiv API](https://api.biorxiv.org/), built on [bibliofabric](https://github.com/utsmok/bibliofabric). It reads preprint metadata by DOI and by date range, the links from preprints to the journal articles they became, preprints by funder, and the content and usage statistics. It ships an async client and a generated sync twin with the same API. The API needs no credentials.

The name is the Latin *prodromus*, a forerunner: a preprint comes before the published article.

## Install

```bash
uv sync --all-packages  # inside the bibliofabric workspace
```

## Quick start

```python
import asyncio

from prodromus import ProdromusClient


async def main():
    async with ProdromusClient() as client:
        versions = await client.details.get("10.1101/339747")
        print([(v.version, v.date, v.published_doi) for v in versions])

        page = await client.details.search("medrxiv", "2026-11-01", "2026-11-01")
        print(page.total, [p.title for p in page.results])

        async for link in client.published.iterate(
            "biorxiv", "2026-11-01", "2026-11-07"
        ):
            print(link.preprint, "->", link.published_doi, link.published_journal)


asyncio.run(main())
```

## What it covers

| Attribute | Routes |
|---|---|
| `details` | `/details/{server}/{doi}/na/json`, `/details/{server}/{start}/{end}/{cursor}`, and the newest posts (`/details/{server}/{N}` and `/{N}d`) |
| `published` | `/pubs/{server}/...` (by DOI or date range), `/publisher/{prefix}/...`, and `/pub/...` |
| `funders` | `/funder/{server}/{start}/{end}/{ror_id}/{cursor}` |
| `statistics` | `/sum/{m,y}` and `/usage/{m,y}/{server}` |

Date ranges page through the cursor in the path (30 records per page on `details`, 100 elsewhere); `iterate()` follows it to the end. A `category` argument filters `details` and `funders` by subject category.

## Settings

Settings load from the environment with the `PRODROMUS_` prefix. The API publishes no rate limit; the client defaults to one request per second over one connection.

## License

MIT. See [LICENSE](LICENSE).
