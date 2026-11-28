# diurnalia

diurnalia is a placeholder name. The package will be renamed before its first release.

diurnalia is a Python client for the [DOAJ API v4](https://doaj.org/api/docs), the API of the [Directory of Open Access Journals](https://doaj.org), built on [bibliofabric](https://github.com/utsmok/bibliofabric). It types the journal and article search routes with Pydantic models, resolves journals by ISSN and articles by DOI through the search route, and enforces the paging limits the API imposes. It ships an async client and a generated sync twin with the same API. The search routes need no credentials.

## Install

```bash
uv add diurnalia
```

Requires Python 3.12 or newer.

## Quick start

```python
import asyncio
from diurnalia import DiurnaliaClient


async def main():
    async with DiurnaliaClient() as client:
        journal = await client.journals.get("1932-6203")
        print(journal.title, journal.publisher_name)

        page = await client.journals.search(query="title:plos")
        print(page.total, [journal.title for journal in page.results])

        article = await client.articles.get("10.3389/fpubh.2020.00115")
        print(article.doi, article.bibjson.journal.title)
        full = await client.journals.get_by_id(journal.id)
        print(full.es_type, full.admin.in_doaj)


asyncio.run(main())
```

`client.journals` and `client.articles` each expose `get()`, `get_by_id()`, `exists()`, `search()`, `iterate()`, `collect()`, `first()`, and `count()`. `get()` takes an ISSN for journals and a DOI for articles and runs a fielded search, because DOAJ has no route for those identifiers. `get_by_id()` takes the DOAJ record id that every result carries as `id` and returns the full record from the record route.

## Query syntax

The query is an Elasticsearch query string. Fielded clauses use the short forms `title`, `issn`, `doi`, `publisher`, `license`, and `abstract`, or the full dot notation such as `bibjson.journal.title.exact:"Journal of Science"`. Clauses combine with `AND`, `OR`, and `ANDNOT`, and ranges use `[2015-01-01 TO 2016-01-01]`. Wildcards, fuzzy (`~`), regex, and proximity searches are disabled by DOAJ and answer 400.

```python
page = await client.journals.search(query='language:EN AND license:"CC BY"')
page = await client.articles.search(
    query="subject.term:medicine AND created_date:[2024-01-01 TO 2025-01-01]"
)
```

## Paging limits

`pageSize` defaults to 10 and the API clamps it to 50. A query reaches at most 1000 records: `(page - 1) * pageSize + pageSize` must stay within 1000, so the last full page at `pageSize=50` is page 20. `iterate()` pages at 50 and the client raises `ConfigurationError` when a page would go beyond the cap. DOAJ serves everything else through its [public data dump](https://doaj.org/docs/public-data-dump/).

## Sync usage

`DiurnaliaSyncClient` is generated from the async source and behaves the same. The sync client uses plain `httpx.Client` and never starts or touches an event loop, so it works in scripts, in Jupyter, in threads, and when called from inside a running event loop.

```python
from diurnalia import DiurnaliaSyncClient

with DiurnaliaSyncClient() as client:
    for article in client.articles.iterate(query="title:hunger", limit=100):
        print(article.doi)
```

## Settings

`DiurnaliaSettings` loads from environment variables prefixed with `DIURNALIA_` and from a `.env` file in the working directory. `DIURNALIA_MAX_REQUESTS_PER_SECOND` (default 1) and `DIURNALIA_MAX_CONCURRENCY` (default 2) set the request pace. DOAJ documents a rate limit of two requests per second on all API routes with bursts of up to five; the default stays at half of it. The shared fields of `bibliofabric.config.BaseApiSettings` also apply, such as `DIURNALIA_TIMEOUT`, `DIURNALIA_MAX_RETRIES`, `DIURNALIA_MAX_RETRY_WAIT`, and `DIURNALIA_USER_AGENT`.

## Where to go next

- [Journals](journals.md) covers the journal record and the search route.
- [Articles](articles.md) covers the article record and the DOI lookup.
- [Upstream quirks](upstream-quirks.md) lists what the live API does differently from its documentation.
