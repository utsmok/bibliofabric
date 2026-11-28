# europaea

europaea is a placeholder name. The package will be renamed before its first release.

europaea is a Python client for the [Europe PMC REST web services](https://europepmc.org/RestfulWebService), the [annotations API](https://europepmc.org/AnnotationsApi), and the [grants API](https://europepmc.org/GristAPI), built on [bibliofabric](https://github.com/utsmok/bibliofabric). It types the article search (cursor paging, sorting, `resultType=lite|core`), the per-article routes, annotations, grants, profiles, and the preprint subset with Pydantic models. It ships an async client and a generated sync twin with the same API. The APIs need no credentials.

## Install

```bash
uv add europaea
```

Requires Python 3.12 or newer.

## Quick start

```python
import asyncio
from europaea import EuropaeaClient


async def main():
    async with EuropaeaClient() as client:
        page = await client.search.search(
            query="DOI:10.1038/nature12373", result_type="core", page_size=1
        )
        article = page.results[0]
        print(article.title, article.cited_by_count)

        references = await client.articles.references(
            "MED:23903748", page=1, page_size=5
        )
        print(references.total, [ref.title for ref in references.results])

        annotations = await client.annotations.by_article_ids(
            "MED:23903748", type="Chemicals"
        )
        print(annotations[0].annotations[0].exact)

        async for record in client.search.iterate(query="nanodiamond", page_size=100):
            print(record.id, record.source)


asyncio.run(main())
```

## Sync usage

The generated `EuropaeaSyncClient` has the same methods without `async` and `await`:

```python
from europaea import EuropaeaSyncClient

with EuropaeaSyncClient() as client:
    page = client.search.search(query="DOI:10.1038/nature12373", result_type="core")
    print(page.results[0].title)

    for record in client.search.iterate(query="nanodiamond", page_size=100):
        print(record.id, record.source)
```

## Settings

`EuropaeaSettings` loads from environment variables prefixed with `EUROPAEA_` and from a `.env` file in the working directory. `EUROPAEA_MAX_REQUESTS_PER_SECOND` (default 3) and `EUROPAEA_MAX_CONCURRENCY` (default 2) set the request pace. Europe PMC publishes no rate limit, so these defaults are a courtesy. The shared fields of `bibliofabric.config.BaseApiSettings` also apply, such as `EUROPAEA_TIMEOUT`, `EUROPAEA_MAX_RETRIES`, `EUROPAEA_MAX_RETRY_WAIT`, and `EUROPAEA_USER_AGENT`.

A search can take about ten seconds. The shared timeout default of 30 seconds covers that.

## Where to go next

- [Search](search.md) covers the query string, `resultType`, sorting, and cursor paging.
- [Articles](articles.md) covers article records, full text, references, citations, and data links.
- [Annotations](annotations.md) covers the annotations API.
- [Grants, profiles, and preprints](grants-profiles-preprints.md) covers the grants API and the profile and preprint searches.
- [Upstream quirks](upstream-quirks.md) lists what the live API does differently from its documentation.
- The [API reference](reference.md) is generated from the source.
