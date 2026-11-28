# diurnalia

diurnalia is not yet published on PyPI; until its first release it installs from the bibliofabric workspace.

diurnalia is a Python client for the [DOAJ API v4](https://doaj.org/api/docs), built on [bibliofabric](https://github.com/utsmok/bibliofabric). It types the journal and article search routes with Pydantic models, resolves journals by ISSN and articles by DOI, and enforces the paging limits the API imposes. It ships an async client and a generated sync twin with the same API. The search routes need no credentials.

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
        print(article.doi)


asyncio.run(main())
```

## Where to go next

- [Journals](journals.md) covers the journal record, search, sorting, and the ISSN lookup.
- [Articles](articles.md) covers the article record and the DOI lookup.
- [Upstream quirks](upstream-quirks.md) lists what the live API does differently from its documentation.
