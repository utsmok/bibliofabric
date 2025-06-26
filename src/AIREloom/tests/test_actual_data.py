"""
End-to-end tests that perform real requests to the OpenAIRE API.

These tests are designed to validate the entire workflow, from client instantiation
to data parsing and comparison with raw API responses. They are marked as asyncio
and are intended to be run in a controlled environment with access to the OpenAIRE API.

To run these tests, you might need to set up authentication credentials in a .env file.
For example, create a .env file in the root of the project with the following content:
AIRELOOM_OPENAIRE_API_TOKEN="your_token"
"""

from collections.abc import Coroutine
from datetime import date, datetime
from typing import Any

import httpx
import pytest
from bibliofabric.log_config import configure_logging, logger
from rich import print

from aireloom import AireloomSession
from aireloom.endpoints import (
    DataSourcesFilters,
    OrganizationsFilters,
    ProjectsFilters,
    ResearchProductsFilters,
    ScholixFilters,
)
from aireloom.models.base import ApiResponse
from aireloom.models.research_product import ResearchProductResponse

# --- Configuration & Setup ---

configure_logging()


# --- Helper Functions ---


async def get_raw_data(url: str, params: dict) -> dict[str, Any]:
    """Fetches raw data from a given URL using httpx."""
    async with httpx.AsyncClient() as client:
        logger.debug(f"Requesting raw data from URL: {url} with params: {params}")
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


def compare_dicts(aireloom_dict: dict, raw_dict: dict) -> None:
    """
       Recursively compares a dictionary parsed by the Aireloom client with a raw
       dictionary from the API.

       It ensures that every key-value pair in the raw dictionary exists and matches
    in
       the Aireloom-parsed dictionary.
    """
    for key, raw_value in raw_dict.items():
        # The API uses 'mainTitle' but the model uses 'title'
        if key == "mainTitle":
            key = "title"

        if key not in aireloom_dict and raw_value is not None:
            raise AssertionError(
                f"Key '{key}' from raw_data not found in aireloom_dict"
            )

        aireloom_value = aireloom_dict.get(key)

        if isinstance(raw_value, dict):
            assert isinstance(aireloom_value, dict), (
                f"Type mismatch for key '{key}': expected dict, got {type(aireloom_value)}"
            )
            compare_dicts(aireloom_value, raw_value)
        elif isinstance(raw_value, list):
            assert isinstance(aireloom_value, list), (
                f"Type mismatch for key '{key}': expected list, got {type(aireloom_value)}"
            )
            compare_lists(aireloom_value, raw_value)
        else:
            assert aireloom_value == raw_value, (
                f"Value mismatch for key '{key}': {aireloom_value} != {raw_value}"
            )


def compare_lists(aireloom_list: list, raw_list: list) -> None:
    """
    Recursively compares a list parsed by the Aireloom client with a raw list
    from the API.
    """
    assert len(aireloom_list) == len(raw_list), (
        f"Lists have different lengths: {len(aireloom_list)} != {len(raw_list)}"
    )
    for aireloom_item, raw_item in zip(aireloom_list, raw_list, strict=False):
        if isinstance(raw_item, dict):
            assert isinstance(aireloom_item, dict), (
                f"Type mismatch in list: expected dict, got {type(aireloom_item)}"
            )
            compare_dicts(aireloom_item, raw_item)
        elif isinstance(raw_item, list):
            assert isinstance(aireloom_item, list), (
                f"Type mismatch in list: expected list, got {type(aireloom_item)}"
            )
            compare_lists(aireloom_item, raw_item)
        else:
            assert aireloom_item == raw_item, (
                f"Items do not match: {aireloom_item} != {raw_item}"
            )


def compare_models_with_raw(
    aireloom_response: ApiResponse, raw_response: dict[str, Any]
) -> None:
    """
    Compares the Aireloom client's parsed Pydantic models with the raw API response.
    """
    assert aireloom_response.results is not None
    assert "results" in raw_response
    assert len(aireloom_response.results) == len(raw_response["results"]), (
        "Number of results does not match"
    )

    for aireloom_item, raw_item in zip(
        aireloom_response.results, raw_response["results"], strict=False
    ):
        try:
            aireloom_dict = aireloom_item.model_dump(exclude_unset=True)
            compare_dicts(aireloom_dict, raw_item)
        except AssertionError as e:
            logger.warning(f"Mismatch found in item {aireloom_item.id}: {e}")
            print("============= AIREloom Product ==============")
            print(aireloom_item.model_dump_json(indent=2))
            print("============= Raw Product ==============")
            print(raw_item)
            raise


# --- Fixtures ---


@pytest.fixture(scope="function")
async def aireloom_session() -> Coroutine[Any, Any, AireloomSession]:
    """Provides an AireloomSession for the entire test module."""
    async with AireloomSession(timeout=30) as session:
        yield session


@pytest.fixture(scope="function")
async def initial_research_products(
    aireloom_session: AireloomSession,
) -> ResearchProductResponse:
    """
    Performs an initial search for research products to be used as a data
    source for other tests.
    """
    filters = ResearchProductsFilters(
        authorOrcid="0000-0003-0581-2668",
        fromPublicationDate=datetime(2020, 1, 1).date(),
    )

    response = await aireloom_session.research_products.search(
        filters=filters, page_size=100
    )
    assert response is not None and response.results is not None
    return response


# --- Test Classes ---


class TestResearchProducts:
    """Tests for the ResearchProducts endpoint."""

    async def test_compare_with_raw_data(
        self,
        aireloom_session: AireloomSession,
        initial_research_products: ResearchProductResponse,
    ):
        """
        Compares the client's output for research products with raw data from httpx.
        """
        filters = ResearchProductsFilters(
            authorOrcid="0000-0003-0581-2668",
            fromPublicationDate=datetime(2020, 1, 1).date(),
        )

        params = {
            k: v.strftime("%Y-%m-%d") if isinstance(v, date) else v
            for k, v in filters.model_dump(exclude_none=True).items()
        }
        params["pageSize"] = 100

        raw_data = await get_raw_data(
            aireloom_session.research_products._api_client._base_url
            + "/researchProducts",
            params=params,
        )

        compare_models_with_raw(initial_research_products, raw_data)


@pytest.mark.asyncio
class TestRelatedEndpoints:
    """
    Tests for endpoints that rely on data from the initial research products search.
    """

    async def test_projects_endpoint(
        self,
        aireloom_session: AireloomSession,
        initial_research_products: ResearchProductResponse,
    ):
        """Tests fetching projects."""

        filters = ProjectsFilters(relOrganizationName="Universiteit Twente")
        projects_response = await aireloom_session.projects.search(
            filters=filters, page_size=100
        )

        assert projects_response is not None and projects_response.results is not None

        assert len(projects_response.results) == 100, (
            f"Expected 100 projects, got {len(projects_response.results)}"
        )

        # Compare with raw data
        params = filters.model_dump(exclude_none=True)
        params["pageSize"] = 100
        raw_data = await get_raw_data(
            aireloom_session.projects._api_client._base_url + "/projects", params=params
        )
        compare_models_with_raw(projects_response, raw_data)

    async def test_organizations_endpoint(
        self,
        aireloom_session: AireloomSession,
        initial_research_products: ResearchProductResponse,
    ):
        """Tests fetching organizations"""

        filters = OrganizationsFilters(legalName="Universiteit Twente")
        orgs_response = await aireloom_session.organizations.search(
            filters=filters, page_size=100
        )

        assert orgs_response is not None and orgs_response.results is not None
        assert len(orgs_response.results) == 100, (
            f"Expected 100 organizations, got {len(orgs_response.results)}"
        )
        # Compare with raw data
        params = filters.model_dump(exclude_none=True)
        params["pageSize"] = 100
        raw_data = await get_raw_data(
            aireloom_session.organizations._api_client._base_url + "/organizations",
            params=params,
        )
        compare_models_with_raw(orgs_response, raw_data)

    async def test_data_sources_endpoint(
        self,
        aireloom_session: AireloomSession,
        initial_research_products: ResearchProductResponse,
    ):
        """Tests fetching data sources."""

        filters = DataSourcesFilters(search="twente")
        ds_response = await aireloom_session.data_sources.search(
            filters=filters, page_size=4
        )

        assert ds_response is not None and ds_response.results is not None
        assert len(ds_response.results) == 4, (
            f"Expected 4 data sources, got {len(ds_response.results)}"
        )
        # Compare with raw data
        params = filters.model_dump(exclude_none=True)
        params["pageSize"] = 4
        raw_data = await get_raw_data(
            aireloom_session.data_sources._api_client._base_url + "/dataSources",
            params=params,
        )
        compare_models_with_raw(ds_response, raw_data)

    async def test_scholix_endpoint(
        self,
        aireloom_session: AireloomSession,
        initial_research_products: ResearchProductResponse,
    ):
        """Tests fetching Scholix links."""

        print(f"Found {len(initial_research_products.results)} research products.")
        dois = []
        for prod in initial_research_products.results:
            if not prod.pids:
                continue
            print(f"Product ID: {prod.id}, PIDs: {[pid for pid in prod.pids]}")
            for pid in prod.pids:
                if pid.scheme == "doi":
                    dois.append(pid.value)

        dois = list(set(dois))
        assert dois, "No DOIs found in research products!"

        logger.info(f"Found {len(dois)} unique DOIs to test Scholix links.")
        for doi in dois:
            try:
                filters = ScholixFilters(sourcePid=f"doi:{doi}")
                scholix_response = await aireloom_session.scholix.search_links(
                    filters=filters
                )

                assert (
                    scholix_response is not None
                    and scholix_response.results is not None
                )

                # Compare with raw data
                params = {"sourcePid": f"doi:{doi}"}
                raw_data = await get_raw_data(
                    aireloom_session.scholix._api_client._base_url + "/Links",
                    params=params,
                )
                compare_models_with_raw(scholix_response, raw_data)
                break  # Exit after the first successful DOI to avoid rate limits
            except Exception as e:
                logger.error(f"Error processing DOI {doi}: {e}")
                continue
