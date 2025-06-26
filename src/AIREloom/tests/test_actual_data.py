from datetime import date, datetime

import httpx
import pytest
from bibliofabric.log_config import configure_logging, logger
from rich import print

from aireloom import AireloomSession
from aireloom.endpoints import ResearchProductsFilters, ScholixFilters
from aireloom.models.research_product import ResearchProductResponse

configure_logging()
# To run these tests, you might need to set up authentication credentials in a .env file.
# For example, create a .env file in the root of the project with the following content:
# AIRELOOM_OPENAIRE_API_TOKEN="your_token"


class TestActualData:
    retrieved_data: ResearchProductResponse | None = None

    @pytest.mark.asyncio
    async def test_research_products_and_related_entities(self):
        """
        This test performs a real-world scenario:
        1. Searches for research products with specific filters.
        2. Verifies the author of the retrieved products.
        3. Uses the results to test other endpoints (projects, organizations, etc.).
        4. Compares the results from the aireloom client with raw data from httpx.
        """
        async with AireloomSession() as session:
            # 1. Search for research products
            filters = ResearchProductsFilters(
                authorOrcid="0000-0003-0581-2668",
                fromPublicationDate=datetime(2020, 1, 1).date(),
            )

            research_products: ResearchProductResponse = (
                await session.research_products.search(filters=filters, page_size=100)
            )

            assert research_products is not None
            assert research_products.results is not None
            self.retrieved_data = research_products
            # 2. Verify author
            for product in research_products.results:
                # Simplified assertion for debugging
                found_author = False
                assert product.authors is not None

                for author in product.authors:
                    if (
                        author.pid
                        and author.pid.id
                        and author.pid.id.value == "0000-0003-0581-2668"
                    ):
                        found_author = True
                        break
                assert any(
                    any(
                        pid and pid.id and pid.id.value == "0000-0003-0581-2668"
                        for pid in (
                            author.pid if isinstance(author.pid, list) else [author.pid]
                        )
                        if author.pid is not None
                    )
                    for author in product.authors
                ), (
                    f"Author with ORCID 0000-0003-0581-2668 not found in product {product.id}"
                )
                print(
                    f"Authors for product {product.id}: {product.authors}"
                )  # Debugging print

            # 3. Test other endpoints using the retrieved data
            if research_products.results:
                first_product = research_products.results[0]

                # Get a project (if available)
                if hasattr(first_product, "project") and first_product.project:
                    project_id = first_product.project.id
                    project = await session.projects.get(project_id)
                    assert project.id == project_id

                # Get an organization (if available)
                if (
                    hasattr(first_product, "organizations")
                    and first_product.organizations
                ):
                    organisation_id = first_product.organizations[0].id
                    organisation = await session.organizations.get(organisation_id)
                    assert organisation.id == organisation_id

                # Get a data source (if available)
                if hasattr(first_product, "datasource") and first_product.datasource:
                    datasource_id = first_product.datasource.id
                    datasource = await session.data_sources.get(datasource_id)
                    assert datasource.id == datasource_id

                # Get scholix data (if DOI available)
                doi = None
                if first_product.pids:
                    for pid in first_product.pids:
                        if pid and pid.id and pid.id.scheme == "doi":
                            doi = pid.id.value
                            break
                if doi:
                    scholix_filters = ScholixFilters(sourcePid=f"doi:{doi}")
                    scholix_links = await session.scholix.search_links(
                        filters=scholix_filters
                    )
                    assert scholix_links is not None

    async def _get_raw_data(self, url: str, params: dict):
        async with httpx.AsyncClient() as client:
            print(f"Raw data request URL: {url} with params: {params}")
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    @pytest.mark.asyncio
    async def test_compare_with_raw_data(self):
        """
        Compares the output of the aireloom client with raw data from httpx.
        """
        async with AireloomSession() as session:
            # Ensure we have retrieved data from the previous test
            if self.retrieved_data is None:
                filters = ResearchProductsFilters(
                    authorOrcid="0000-0003-0581-2668",
                    fromPublicationDate=datetime(2020, 1, 1).date(),
                )

                research_products: ResearchProductResponse = (
                    await session.research_products.search(
                        filters=filters, page_size=100
                    )
                )

                assert research_products is not None
                assert research_products.results is not None
                self.retrieved_data = research_products

            params = {
                k: v.strftime("%Y-%m-%d") if isinstance(v, date) else v
                for k, v in filters.model_dump(exclude_none=True).items()
            }
            params["pageSize"] = 100
            # Get raw data from httpx
            raw_data = await self._get_raw_data(
                session.research_products._api_client._base_url + "/researchProducts",
                params=params,
            )

            # Compare the results
            assert self.retrieved_data is not None
            assert self.retrieved_data.results is not None

            # Ensure the number of results matches
            assert len(self.retrieved_data.results) == len(raw_data["results"])

            # Compare basic fields for each product
            for aireloom_product, raw_product in zip(
                self.retrieved_data.results, raw_data["results"], strict=False
            ):
                aireloom_dict = aireloom_product.model_dump()
                aireloom_dict = dict(sorted(aireloom_dict.items()))
                raw_dict = dict(sorted(raw_product.items()))

                # we want to compare json structures aireloom_dict and raw_dict
                # We start with raw_dict: all fields and keys should in this dict should be present in aireloom_dict in the same way
                # aireloom_dict can also have additiona fields, we can ignore that.

                # if a field/key is in raw_dict but not in aireloom_dict: assertion error.

                # for this we need a recursive function that compares the two dicts. Also, the nested dicts can hold dicts/lists as values, so handle that as well.

                def compare_dicts(a, b):
                    assert isinstance(a, dict) and isinstance(b, dict), (
                        f"received value from raw_data is dict, but aireloom_dict isn't: {a}"
                    )
                    for key, value in b.items():
                        assert key in a, (
                            f"Key '{key}' from raw_data not found in aireloom_dict"
                        )
                        if isinstance(value, dict):
                            compare_dicts(a[key], value)
                        elif isinstance(value, list):
                            for item in value:
                                assert item in a[key], (
                                    f"Item '{item}' from raw_data not found in aireloom_dict[{key}]"
                                )
                        else:
                            assert a[key] == value, (
                                f"Value mismatch for key '{key}': {a[key]} != {value}"
                            )

                def compare_lists(a, b):
                    assert isinstance(a, list) and isinstance(b, list), (
                        "Both arguments must be lists"
                    )
                    assert len(a) == len(b), (
                        f"Lists have different lengths: {len(a)} != {len(b)}"
                    )

                    for item_a, item_b in zip(a, b, strict=False):
                        if isinstance(item_a, dict) and isinstance(item_b, dict):
                            compare_dicts(item_a, item_b)
                        elif isinstance(item_a, list) and isinstance(item_b, list):
                            compare_lists(item_a, item_b)
                        else:
                            assert item_a == item_b, (
                                f"Items do not match: {item_a} != {item_b}"
                            )

                try:
                    for key, v in raw_dict.items():
                        if key == "mainTitle":
                            key = "title"
                        if isinstance(v, dict):
                            compare_dicts(aireloom_dict.get(key), v)
                        elif isinstance(v, list):
                            compare_lists(aireloom_dict.get(key), v)
                        else:
                            assert aireloom_dict.get(key) == v, (
                                f"Value mismatch for key '{key}': {aireloom_dict.get(key)} != {v}"
                            )

                except AssertionError as e:
                    logger.warning(f"Mismatch found in {key}: {e}")
                    print("============= AIREloom Product =============")
                    print(aireloom_dict)
                    print("============= Raw Product =============")
                    print(raw_dict)
                    raise e
