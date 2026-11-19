# Stavrophora

**Python interface for the Crossref API**, built on [bibliofabric](https://github.com/utsmok/bibliofabric).

Stavrophora is a fully-typed, async-first Python client for the [Crossref REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/). It wraps the works, journals, funders, members, types, prefixes and licenses endpoints with Pydantic models, Crossref filter serialization, and cursor-based pagination.

The [project README](https://github.com/utsmok/stavrophora) is the canonical documentation: features, installation, quick start, usage examples, configuration, and the live-verified Crossref API quirks the client defends against.

```python
import asyncio
from stavrophora import StavrophoraSession


async def main():
    async with StavrophoraSession(mailto="you@example.org") as session:
        work = await session.works.get("10.1038/nature12373")
        print(work.primary_title)


asyncio.run(main())
```
