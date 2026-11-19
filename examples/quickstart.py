"""Core stavrophora usage: get, search, and cursor iteration.

Run with a polite-pool email:

    STAVROPHORA_MAILTO=you@example.org uv run python examples/quickstart.py
"""

import asyncio
import os

from stavrophora import StavrophoraClient, WorksFilters


async def main() -> None:
    mailto = os.environ.get("STAVROPHORA_MAILTO")
    if not mailto:
        raise SystemExit("set STAVROPHORA_MAILTO to run this example")

    async with StavrophoraClient(mailto=mailto) as client:
        work = await client.works.get("10.1038/nature12373")
        print(work.doi, work.primary_title)

        page = await client.works.search(
            WorksFilters(type="journal-article", has_abstract=True),
            query="proteomics",
            sort="is-referenced-by-count:desc",
            select=["DOI", "title", "is-referenced-by-count"],
            page_size=5,
        )
        for work in page.results:
            print(work.doi, work.is_referenced_by_count, work.primary_title)

        async for work in client.works.iterate(query="crispr", limit=10):
            print("iterated", work.doi)


if __name__ == "__main__":
    asyncio.run(main())
