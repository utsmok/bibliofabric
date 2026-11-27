"""Quick-start example: search research products and walk projects.

Run with `uv run python packages/aireloom/examples/quickstart.py`. Anonymous
access works for read-only calls; set AIRELOOM_OPENAIRE_CLIENT_ID and
AIRELOOM_OPENAIRE_CLIENT_SECRET for the registered-service quota.
"""

import asyncio

from aireloom import AireloomClient, ResearchProductsFilters


async def main() -> None:
    async with AireloomClient() as client:
        page = await client.research_products.search(
            ResearchProductsFilters(type="publication"),
            query="graph neural networks",
            page_size=5,
        )
        print(f"{page.total} matches")
        for product in page.results:
            print(product.id, product.mainTitle)

        async for project in client.projects.iterate(limit=10):
            print(project.id, project.code or project.acronym)


if __name__ == "__main__":
    asyncio.run(main())
