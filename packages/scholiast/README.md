# scholiast: Python client for the Semantic Scholar APIs (async and sync)

Samuel Mok -- 2026

`scholiast` is a placeholder name. The package will be renamed
before its first release.

scholiast is a Python client for the Semantic Scholar Academic
Graph API (papers, authors, citations, patents, snippets), the
Recommendations API, and the Datasets API, built on
[bibliofabric](https://github.com/utsmok/bibliofabric). The async client
is the source of truth; a generated sync twin
(`ScholiastSyncClient`) offers the same API without an event
loop. The API key is optional: with one the client sends `x-api-key`,
without one it runs on the shared anonymous pool.

**Docs:** [utsmok.github.io/bibliofabric/scholiast](https://utsmok.github.io/bibliofabric/scholiast/) -- **License:** MIT

## Features

- **Async and sync**: built on `httpx`; the generated sync twin has the same API
- **Typed throughout**: Pydantic v2 models for papers, authors, citations,
  references, snippets, patents, recommendations, and dataset releases,
  PEP 561 `py.typed` marker
- **Every id form**: get papers by S2 id, `DOI:`, `ARXIV:`, `PMID:`,
  `PMCID:`, `MAG:`, `ACL:`, `PubMedCentral:`, `CorpusId:`, and `URL:`
- **Search at both scales**: relevance search with filters and offsets, and
  bulk search (1000 records per call) with automatic token continuation
- **Batch reads**: `POST /paper/batch` and `/author/batch` with chunking,
  retries, and `null` entries for unknown ids dropped
- **Citations and references**: context snippets, intents, and influence
  flags, paged by offset
- **Recommendations**: related papers for one id or for a positive/negative
  list
- **Datasets**: releases, dataset metadata with pre-signed file URLs, and
  diffs between releases
- **Gentle by default**: 1 request per second, the guaranteed per-key rate,
  which also survives the contended anonymous pool

## Installation

```bash
uv add scholiast
```

Requires Python >=3.12.

## Quick Start

```python
import asyncio
from scholiast import ScholiastClient


async def main():
    async with ScholiastClient() as client:
        # Get one paper by any id form; fields select what comes back
        paper = await client.papers.get("DOI:10.1038/nature12373")
        print(paper.title, paper.year, paper.citationCount)

        # Relevance search with filters
        page = await client.papers.search(
            {"year": "2020-2023", "minCitationCount": 50},
            query="photosynthesis",
            fields=["title", "year"],
            page_size=20,
        )
        print(page.total, len(page.results))

        # Bulk search, 1000 records per call, token followed automatically
        papers = [
            paper async for paper in client.papers.bulk_iterate("crispr", limit=5000)
        ]

        # Batch: unknown ids come back null and are dropped
        papers = await client.papers.batch(
            ["DOI:10.1038/nature12373", "ARXIV:1304.1068"], fields=["title"]
        )

        # Citations with contexts and intents
        citations = await client.papers.citations(
            "DOI:10.1038/nature12373", fields=["contexts", "intents"], limit=100
        )


asyncio.run(main())
```

## Authentication

Set `SCHOLIAST_API_KEY` in the environment (or a `.env` file) and
the client sends it as the `x-api-key` header on every request. Without a
key the client works on the shared anonymous pool, where requests can
answer HTTP 429; the mapping of 429 to `bibliofabric.RateLimitError` is
part of the framework. The client paces itself at 1 request per second by
default, which works in both modes. Some fields (`embedding`,
`openAccessDoi`) and routes (dataset files and diffs, snippet search)
need a key regardless.

## Resources

| Client | Routes |
|---|---|
| `client.papers` | `/paper` get (all id forms), `/paper/search`, `/paper/search/bulk`, `POST /paper/batch`, `/citations`, `/references`, `/authors`, `/paper/autocomplete`, `/paper/search/match` |
| `client.authors` | `/author` get, `/author/search`, `/author/{id}/papers`, `POST /author/batch` |
| `client.recommendations` | `/recommendations/v1/papers/forpaper/{id}` and `POST /papers/` |
| `client.datasets` | `/datasets/v1/release`, `/release/{id}`, `/release/{id}/dataset/{name}`, `/diffs/{a}/to/{b}/{name}` |
| `client.snippets` | `/snippet/search` (needs a key) |
| `client.patents` | `/patent/{ucid}`, `/patent/search`, `/patent/outbound-citations/{paper_id}` |

## Development

```bash
uv sync --all-packages --all-groups
uv run pytest packages/scholiast/tests          # offline suite
uv run pytest -m live_api packages/scholiast/tests  # live smoke tests
uv run python scripts/unasync.py --package scholiast
```

The live tests need no credentials: they run keyless on the anonymous pool
and skip with `rate limited` when the pool throttles them.

## License

MIT
