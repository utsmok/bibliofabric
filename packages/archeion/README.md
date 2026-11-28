# archeion

archeion is not yet published on PyPI; until its first release it installs from the bibliofabric workspace.

archeion is a Python client for the [arXiv API](https://info.arxiv.org/help/api/), built on [bibliofabric](https://github.com/utsmok/bibliofabric). It searches arXiv and looks up papers by id through the query route, parses the Atom feeds into Pydantic models, and paces requests at one every three seconds over one connection, as the [arXiv terms of use](https://info.arxiv.org/help/api/tou.html) ask. It ships an async client and a generated sync twin with the same API. The API needs no credentials.

The name is the Greek ἀρχεῖον, the root of "archive", and the X of arXiv is the Greek letter chi.

## Install

```bash
uv sync --all-packages  # inside the bibliofabric workspace
```

## Quick start

```python
import asyncio

from archeion import ArcheionClient


async def main():
    async with ArcheionClient() as client:
        paper = await client.query.get("1706.03762")
        print(paper.title, paper.version, paper.primary_category, paper.pdf_url)

        page = await client.query.search(
            "ti:transformer AND cat:cs.CL", sort_by="submittedDate", page_size=5
        )
        print(page.total, [record.arxiv_id for record in page.results])

        found = await client.query.batch_get(["1706.03762v1", "hep-th/9711200"])
        print(sorted(found))

        async for record in client.query.iterate("au:maldacena", limit=20):
            print(record.versioned_id, record.journal_ref)


asyncio.run(main())
```

## What it covers

`client.query` wraps `GET /api/query`:

| Method | What it does |
|---|---|
| `search(query, ids=, sort_by=, sort_order=, start=, page_size=)` | One page of results, `page.total` from `opensearch:totalResults` |
| `iterate(query, ids=, page_size=, limit=)` | Every result up to `limit` or the documented reach of 30,000 |
| `get(id)` | One paper by id, newest version unless the id has one |
| `batch_get(ids)` | Many papers in `id_list` requests of 100, keyed by the requested id |
| `count(query)` | The total of a query |

Each result is an `ArxivEntry` with `title`, `summary`, `authors` (names and affiliations), `published` (version 1), `updated` (this version), `categories`, `primary_category`, `comment`, `journal_ref`, `doi`, and `links`, plus the properties `arxiv_id`, `versioned_id`, `version`, `pdf_url`, and `author_names`.

The arXiv OAI-PMH interface and the bulk data on Amazon S3 are not wrapped yet; see the [deferred list](../../docs/roadmap/deferred.md).

## Settings

Settings load from the environment with the `ARCHEION_` prefix. The defaults follow the arXiv terms of use: `ARCHEION_MAX_REQUESTS_PER_SECOND=0.333` and `ARCHEION_MAX_CONCURRENCY=1`.

## License

MIT. See [LICENSE](LICENSE).
