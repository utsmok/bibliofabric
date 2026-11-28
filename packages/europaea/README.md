# europaea

europaea is not yet published on PyPI; until its first release it installs from the bibliofabric workspace.

europaea is a Python client for the [Europe PMC REST web services](https://europepmc.org/RestfulWebService), built on [bibliofabric](https://github.com/utsmok/bibliofabric). It covers the article search, the per-article routes (references, citations, database and data links, JATS full text, book XML, supplementary files, evaluations), the annotations API, the grants (Grist) API, the profile endpoint, and the preprint subset. It ships an async client and a generated sync twin with the same API. The APIs need no credentials.

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

## Client layout

| Attribute | Routes |
|---|---|
| `client.search` | `/search` and `POST /searchPOST` (query syntax, `resultType`, cursor paging, sort, synonym) and `/fields` |
| `client.articles` | `/article/{source}/{id}`, `/fullTextXML`, `/bookXML`, `/supplementaryFiles`, `/references`, `/citations`, `/databaseLinks`, `/datalinks`, `/labsLinks`, `/evaluations`, `POST /status-update-search` |
| `client.annotations` | `annotations_api`: by article ids, entity, provider, relationship, section and type |
| `client.grants` | The grants (Grist) API (`GristAPI/rest/get`) |
| `client.profiles` | `/profile` and `/fields` |
| `client.preprints` | `/search` scoped to the `SRC:PPR` preprint source |

## Rate limits

The Europe PMC documentation publishes no rate limit and no hard request limit. A search can take several seconds (the client default timeout is 30 seconds for that reason). The client defaults to 3 requests per second and a concurrency of 2; both are tunable through `EuropaeaSettings` (`EUROPAEA_MAX_REQUESTS_PER_SECOND`, `EUROPAEA_MAX_CONCURRENCY`, `EUROPAEA_TIMEOUT`, `EUROPAEA_MAILTO`).

## Docs

- [Search](search.md): query syntax, paging, sorting, result types
- [Articles](articles.md): records, full text XML, references, citations, links
- [Annotations](annotations.md): annotation queries over articles, entities, providers
- [Grants, profiles, and preprints](grants-profiles-preprints.md)
- [Upstream quirks](upstream-quirks.md): live-verified behavior of the APIs
- [API reference](reference.md)

## License

MIT. See [LICENSE](LICENSE).
