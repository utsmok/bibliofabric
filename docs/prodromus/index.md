# prodromus

prodromus is not yet published on PyPI; until its first release it installs from the bibliofabric workspace.

prodromus is a Python client for the [bioRxiv and medRxiv API](https://api.biorxiv.org/), built on [bibliofabric](https://github.com/utsmok/bibliofabric). One client serves both preprint servers. It reads preprint metadata by DOI and by date range, the links from preprints to the journal articles they became, preprints by funder, and the content and usage statistics. It ships an async client and a generated sync twin with the same API. The API needs no credentials.

## Quick start

```python
from prodromus import ProdromusClient

async with ProdromusClient() as client:
    versions = await client.details.get("10.1101/339747")
    [(version.version, version.date) for version in versions]

    async for preprint in client.details.iterate("medrxiv", "2026-11-01", "2026-11-01"):
        preprint.doi, preprint.category, preprint.published_doi
```

## Routes

| Method | Route | Returns |
|---|---|---|
| `details.get(doi, server=)` | `/details/{server}/{doi}/na/json` | every version as `Preprint` |
| `details.search(server, start, end, cursor=, category=)` | `/details/{server}/{start}/{end}/{cursor}` | a page of 30 |
| `details.iterate(server, start, end, category=)` | the same, every page | `Preprint` |
| `details.recent(server, posts= or days=)` | `/details/{server}/{N}` or `/{N}d` | one answer, no paging |
| `published.get(doi, server=)` | `/pubs/{server}/{doi}/na/json` | `PublishedArticle` list; preprint or journal DOI |
| `published.search` / `iterate(server, start, end)` | `/pubs/{server}/{start}/{end}/{cursor}` | pages of 100 |
| `published.by_publisher` / `iterate_by_publisher(prefix, start, end)` | `/publisher/{prefix}/{start}/{end}/{cursor}` | bioRxiv only |
| `published.biorxiv(start, end, cursor=)` | `/pub/{start}/{end}/{cursor}` | bioRxiv only, fewer fields |
| `funders.search` / `iterate(server, ror_id, start, end)` | `/funder/{server}/{start}/{end}/{ror}/{cursor}` | `Preprint` with `funder` declarations |
| `statistics.content(interval)` | `/sum/{m,y}` | `ContentStatistic` list |
| `statistics.usage(server, interval)` | `/usage/{m,y}/{server}` | `UsageStatistic` list |

`server` is `biorxiv` or `medrxiv`. Dates are `YYYY-MM-DD`. `category` filters by subject category, written with spaces or underscores (`cell biology`). The funder route covers posts from 2025-04-10 on.

## Upstream quirks

Checked against the live API on 2026-11-28.

- Errors come back with HTTP 200 and the reason in `messages[0].status`, for example `Both dates must be in yyyy-mm-dd format`. The client raises `ConfigurationError` for them, and treats `no posts found` and `no articles found` as empty answers.
- The newest-posts forms (`/details/biorxiv/45`, `/details/biorxiv/2d`) take no cursor, and the funder route takes no `Nd` form; with them the API answers the date-format error.
- `cursor` is a number on the first page and a string on later pages, and `total` is often a string.
- `authors` is one string with `;` between names (`Preprint.author_list` splits it), `published` is a journal DOI or `NA` (`Preprint.published_doi` reads it), and `version` is a string.
- The API publishes no rate limit; the client defaults to one request per second over one connection (`PRODROMUS_MAX_REQUESTS_PER_SECOND`).

## Reference

::: prodromus.ProdromusClient
    options:
      heading_level: 3
      show_source: false
      members:
        - details
        - published
        - funders
        - statistics

::: prodromus.DetailsClient
    options:
      heading_level: 3
      show_source: false

::: prodromus.PublishedClient
    options:
      heading_level: 3
      show_source: false

::: prodromus.FundersClient
    options:
      heading_level: 3
      show_source: false

::: prodromus.StatisticsClient
    options:
      heading_level: 3
      show_source: false

::: prodromus.Preprint
    options:
      heading_level: 3
      show_source: false

::: prodromus.PublishedArticle
    options:
      heading_level: 3
      show_source: false
