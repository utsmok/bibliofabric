# scholiast

scholiast is not yet published on PyPI; until its first release it installs from the bibliofabric workspace.

scholiast is a Python client for the [Semantic Scholar Academic Graph API](https://api.semanticscholar.org/api-docs/graph), the [Recommendations API](https://api.semanticscholar.org/api-docs/recommendations), and the [Datasets API](https://api.semanticscholar.org/api-docs/datasets), built on [bibliofabric](https://github.com/utsmok/bibliofabric). It types papers, authors, citations, patents, snippets, recommendations, and dataset releases with Pydantic models, paces itself at 1 request per second by default, and works with or without an API key. It ships an async client and a generated sync twin with the same API.

## Install

```bash
uv add scholiast
```

Requires Python 3.12 or newer.

## Authentication

The API key is optional. Set `SCHOLIAST_API_KEY` (or pass
`api_key` to `ScholiastSettings`) and the client sends it as the
`x-api-key` header on every request, which moves you from the shared
anonymous pool to your own 1 request per second allocation. Without a key
the client runs on the shared pool, where any request can answer HTTP 429.
Some fields (`embedding`, `openAccessDoi`) and some routes (dataset file
listings, diffs, snippet search) need a key regardless; the API answers
400 or 401 without one.

## Quick start

```python
import asyncio
from scholiast import ScholiastClient


async def main():
    async with ScholiastClient() as client:
        paper = await client.papers.get("DOI:10.1038/nature12373")
        print(paper.title, paper.year, paper.citationCount)

        page = await client.papers.search(
            query="photosynthesis", fields=["title", "year"], page_size=10
        )
        print(page.total, [paper.title for paper in page.results])

        papers = await client.papers.batch(
            ["DOI:10.1038/nature12373", "ARXIV:1304.1068"], fields=["title"]
        )
        print(len(papers))


asyncio.run(main())
```

`client.papers` exposes `get()`, `exists()`, `search()`, `iterate()`,
`collect()`, `first()`, `count()`, `batch()`, `bulk_search()`,
`bulk_iterate()`, `citations()`, `references()`, `authors()`,
`autocomplete()`, and `search_match()`. `client.authors` exposes `get()`,
`search()`, `iterate()`, `papers()`, and `batch()`. `client.recommendations`
exposes `for_paper()` and `for_list()`. `client.datasets` exposes
`releases()`, `latest()`, `release()`, `dataset()`, and `diffs()`. `client.snippets`
and `client.patents` expose `search()` and `get()` respectively. Start with
[papers](papers.md) and [authors](authors.md).

## Sync usage

`ScholiastSyncClient` is generated from the async source and
behaves the same. The sync client uses plain `httpx.Client` and never
starts or touches an event loop, so it works in scripts, in Jupyter, in
threads, and when called from inside a running event loop.

```python
from scholiast import ScholiastSyncClient

with ScholiastSyncClient() as client:
    paper = client.papers.get("DOI:10.1038/nature12373")
    print(paper.title)
```

## Rate limits

Semantic Scholar publishes 1000 requests per second for the whole
unauthenticated pool and 1 request per second for an API key. The pool is
contended, so keyless callers see HTTP 429 often. The client defaults to 1
request per second and concurrency 1, which is safe in both modes. Raise
`SCHOLIAST_MAX_REQUESTS_PER_SECOND` only if you know your key's
tier. See [upstream quirks](upstream-quirks.md) for what the live API
actually did on 2026-11-27.

## Links

- [Papers](papers.md)
- [Authors](authors.md)
- [Recommendations](recommendations.md)
- [Datasets](datasets.md)
- [Other routes](other-routes.md) (snippets, patents)
- [Upstream quirks](upstream-quirks.md)
- [API reference](reference.md)
