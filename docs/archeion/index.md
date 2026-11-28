# archeion

archeion is not yet published on PyPI; until its first release it installs from the bibliofabric workspace.

archeion is a Python client for the [arXiv API](https://info.arxiv.org/help/api/), built on [bibliofabric](https://github.com/utsmok/bibliofabric). It searches arXiv and looks up papers by id through the query route, parses the Atom feeds into Pydantic models, and paces requests at one every three seconds over one connection, as the [arXiv terms of use](https://info.arxiv.org/help/api/tou.html) ask. It ships an async client and a generated sync twin with the same API. It is the first Wave 2 library of the family.

## Install

```bash
uv sync --all-packages  # inside the bibliofabric workspace
```

## Quick start

```python
from archeion import ArcheionClient

async with ArcheionClient() as client:
    paper = await client.query.get("1706.03762")
    paper.title, paper.version, paper.primary_category, paper.pdf_url

    page = await client.query.search("ti:transformer AND cat:cs.CL", page_size=5)
    page.total, [record.arxiv_id for record in page.results]
```

The sync twin `ArcheionSyncClient` has the same methods without `await`.

## Where to go next

- [Query](query.md) covers search syntax, paging, and lookups by id.
- [Upstream quirks](upstream-quirks.md) lists what the live API does differently from its documentation.
- The [API reference](reference.md) is generated from the source.
