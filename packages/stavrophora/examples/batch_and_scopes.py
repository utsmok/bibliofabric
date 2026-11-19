"""Batch DOI lookup, facets, scoped works, and error handling."""

import asyncio
import os

from bibliofabric.exceptions import NotFoundError

from stavrophora import StavrophoraClient


async def main() -> None:
    mailto = os.environ.get("STAVROPHORA_MAILTO")
    if not mailto:
        raise SystemExit("set STAVROPHORA_MAILTO to run this example")

    async with StavrophoraClient(mailto=mailto) as client:
        works = await client.works.batch_get_by_doi(
            [
                "https://doi.org/10.1038/Nature12373",
                "10.1109/TIP.2009.2037465",
                "10.1/does-not-exist",
            ]
        )
        for doi, work in sorted(works.items()):
            print(doi, work.primary_title)

        facets = await client.works.facets(
            query="crispr", facets=("type-name",), count=5
        )
        print(facets["type-name"])

        page = await client.journals.works("20493630").search(page_size=3)
        for work in page.results:
            print("scoped", work.doi)

        try:
            await client.works.get("10.1/missing")
        except NotFoundError as error:
            print("not found:", error)


if __name__ == "__main__":
    asyncio.run(main())
