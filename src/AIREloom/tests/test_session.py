# tests/test_session.py
import json
import httpx
import urllib.parse
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bibliofabric.auth import (
    ClientCredentialsAuth,
    NoAuth,
    StaticTokenAuth,
)
from bibliofabric.exceptions import BibliofabricError
from dotenv import load_dotenv
from pytest_httpx import HTTPXMock

from aireloom import AireloomSession
from aireloom.constants import (
    OPENAIRE_GRAPH_API_BASE_URL,
    OPENAIRE_SCHOLIX_API_BASE_URL,
    EndpointName,
)
from aireloom.endpoints import (
    DataSourcesFilters,
    OrganizationsFilters,
    ProjectsFilters,
    ResearchProductsFilters,
    ScholixFilters,
)
from aireloom.models import (
    DataSource,
    Organization,
    Project,
    ResearchProduct,
    ScholixRelationship as ScholixLink,  # Alias for test consistency
)
from aireloom.models.base import ApiResponse
from aireloom.models.scholix import ScholixResponse  # Import for Scholix tests
from aireloom.resources import (
    DataSourcesClient,
    OrganizationsClient,
    ProjectsClient,
    ResearchProductsClient,
    ScholixClient,
)

# Load .env file for local testing (e.g., containing AIRELOOM_OPENAIRE_API_TOKEN)
load_dotenv()

# --- Constants ---
KNOWN_PRODUCT_ID = "doi_dedup___::2b3cb7130c506d1c3a05e9160b2c4108"
KNOWN_PRODUCT_TITLE_FRAGMENT = "OpenAIRE Graph"
KNOWN_DOI_WITH_LINKS = "10.5281/zenodo.7668094"
UNKNOWN_PRODUCT_ID = "oai:example.org:nonexistent123"
INVALID_PRODUCT_ID_FORMAT = "not-a-valid-id-format"

# --- Mock Data ---
MOCK_SCHOLIX_RESPONSE = {
    "currentPage": 0,
    "totalLinks": 1,
    "totalPages": 1,
    "result": [
        {
            "LinkProvider": [{"Name": "Example Provider", "AgentId": "example"}],
            "LinkPublicationDate": "2023-01-15T12:00:00Z",
            "RelationshipType": {
                "Name": "References",
                "SubType": "Scholix",
                "SubTypeSchema": "http://example.com/datacite",
            },
            "Source": {
                "Identifier": [{"ID": KNOWN_DOI_WITH_LINKS, "IDScheme": "doi"}],
                "Type": "publication",
                "Title": "Source Title",
                "Creator": [{"Name": "Source Author"}],
                "PublicationDate": "2023",
                "Publisher": [{"Name": "Source Publisher"}],
            },
            "Target": {
                "Identifier": [{"ID": "10.1234/target.dataset", "IDScheme": "doi"}],
                "Type": "dataset",
            },
            "LicenseURL": None,
            "HarvestDate": None,
        }
    ],
}

# --- Basic Initialization Tests ---


@pytest.mark.asyncio
async def test_session_initialization_no_token():
    """Test initializing AireloomSession without providing a token."""
    async with AireloomSession(auth_strategy=NoAuth()) as session:
        assert session is not None
        assert isinstance(session._api_client._auth_strategy, NoAuth)
        assert isinstance(session.research_products, ResearchProductsClient)
        assert isinstance(session.organizations, OrganizationsClient)
        assert isinstance(session.projects, ProjectsClient)
        assert isinstance(session.data_sources, DataSourcesClient)
        assert isinstance(session.scholix, ScholixClient)


@pytest.mark.asyncio
async def test_session_initialization_with_token(api_token):
    """Test initializing AireloomSession with a token (from fixture)."""
    if not api_token:
        pytest.skip("Skipping token test: AIRELOOM_OPENAIRE_API_TOKEN not set.")

    auth_strat = StaticTokenAuth(token=api_token)
    async with AireloomSession(auth_strategy=auth_strat) as session:
        assert session is not None
        assert isinstance(session._api_client._auth_strategy, StaticTokenAuth)
        assert session._api_client._auth_strategy._token == api_token

    # Test token via settings (implicitly via environment variable)
    # AireloomClient inside AireloomSession should pick this up
    async with AireloomSession() as session_env:
        assert session_env is not None
        assert isinstance(session_env._api_client._auth_strategy, StaticTokenAuth)
        assert session_env._api_client._auth_strategy._token == api_token


@pytest.mark.asyncio
async def test_session_initialization_with_custom_timeout():
    """Test initializing AireloomSession with custom timeout."""
    custom_timeout_float = 45.0
    custom_timeout_int = int(custom_timeout_float)  # AireloomSession expects int | None

    async with AireloomSession(
        auth_strategy=NoAuth(), timeout=custom_timeout_int
    ) as session:
        assert session is not None
        assert isinstance(session._api_client._auth_strategy, NoAuth)
        # AireloomClient's _settings will have the updated timeout
        assert session._api_client._settings.request_timeout == custom_timeout_float
        # The internal httpx.AsyncClient will be configured with this timeout
        assert session._api_client._http_client.timeout.read == custom_timeout_float
        assert session._api_client._http_client.timeout.connect == custom_timeout_float


@pytest.mark.asyncio
async def test_session_context_manager_aclose():
    """Test that the async context manager calls aclose on the client."""
    session = AireloomSession()
    initial_client = session._api_client
    assert (
        initial_client._http_client is not None
        and not initial_client._http_client.is_closed
    )

    async with session:
        assert session._api_client is not None
        assert not session._api_client._http_client.is_closed
    assert session._api_client._http_client.is_closed


# --- Integration Tests for Resource Clients via Session ---


# --- ResearchProducts ---
@pytest.mark.asyncio
async def test_session_get_research_product_integration():
    product_id = "rp123"
    token_url = "https://aai.openaire.eu/oidc/token"  # Standard token URL
    expected_url = (
        f"{OPENAIRE_GRAPH_API_BASE_URL}/{EndpointName.RESEARCH_PRODUCTS.value}"
    )

    mock_api_response_json = {
        "results": [
            {
                "id": product_id,
                "title": "Mocked Research Product Title",
                "type": "publication",
                "publicationDate": "2023-01-01",
            }
        ],
        "header": {"numFound": 1, "pageSize": 1},
    }
    auth_strategy = ClientCredentialsAuth(
        client_id="test_id",
        client_secret="test_secret",
        token_url=token_url,
    )
    async with AireloomSession(auth_strategy=auth_strategy) as session:
        with patch("bibliofabric.client.BaseApiClient._request_with_retry", new_callable=AsyncMock) as mock_request_with_retry:
            mock_response = MagicMock(spec=httpx.Response, status_code=200)
            mock_response.json.return_value = mock_api_response_json
            # Mocking the return value to include a third element for attempts
            mock_request_with_retry.return_value = (mock_response, None, 1)
            product = await session.research_products.get(product_id)
    assert isinstance(product, ResearchProduct)
    assert product.id == product_id
    assert product.title == "Mocked Research Product Title"


@pytest.mark.asyncio
async def test_session_search_research_products_integration():
    token_url = "https://aai.openaire.eu/oidc/token"
    expected_url = (
        f"{OPENAIRE_GRAPH_API_BASE_URL}/{EndpointName.RESEARCH_PRODUCTS.value}"
    )

    mock_api_response_json = {
        "header": {
            "page": 1,
            "size": 1,
            "numFound": 1,
            "totalPages": 1,
            "maxPage": 1000,
        },
        "results": [
            {
                "id": "rp456",
                "title": "Searched Research Product",
                "type": "publication",
                "publicationDate": "2023-02-01",
            }
        ],
    }


@pytest.mark.asyncio
async def test_session_iterate_research_products_integration():
    token_url = "https://aai.openaire.eu/oidc/token"
    base_url = f"{OPENAIRE_GRAPH_API_BASE_URL}/{EndpointName.RESEARCH_PRODUCTS.value}"

    mock_response_page1 = {
        "header": {
            "page": 1,
            "size": 1,
            "numFound": 2,
            "totalPages": 2,
            "nextCursor": "cursor1",
        },
        "results": [
            {
                "id": "rp_iter1",
                "title": "Iter Product 1",
                "type": "publication",
                "publicationDate": "2023-03-01",
            }
        ],
    }
    mock_response_page2 = {
        "header": {
            "page": 2,
            "size": 1,
            "numFound": 2,
            "totalPages": 2,
            "nextCursor": None,
        },
        "results": [
            {
                "id": "rp_iter2",
                "title": "Iter Product 2",
                "type": "publication",
                "publicationDate": "2023-03-02",
            }
        ],
    }


# --- Organizations ---
@pytest.mark.asyncio
async def test_session_get_organization_integration():
    token_url = "https://aai.openaire.eu/oidc/token"
    org_id = "org123"
    expected_url = f"{OPENAIRE_GRAPH_API_BASE_URL}/{EndpointName.ORGANIZATIONS.value}"

    # Mock for the token acquisition
    

    mock_api_response_json = {
        "results": [
            {
                "id": org_id,
                "legalName": "Mocked Org Name",
                "country": {"code": "GR", "name": "Greece"},
            }
        ],
        "header": {"numFound": 1, "pageSize": 1},
    }
    auth_strategy = ClientCredentialsAuth(
        client_id="test_id",
        client_secret="test_secret",
        token_url=token_url,
    )
    async with AireloomSession(auth_strategy=auth_strategy) as session:
        with patch("bibliofabric.client.BaseApiClient._request_with_retry", new_callable=AsyncMock) as mock_request_with_retry:
            mock_response = MagicMock(spec=httpx.Response, status_code=200)
            mock_response.json.return_value = mock_api_response_json
            mock_request_with_retry.return_value = (mock_response, None, 1)
            organization = await session.organizations.get(org_id)
    assert isinstance(organization, Organization)
    assert organization.id == org_id
    assert organization.legalName == "Mocked Org Name"


@pytest.mark.asyncio
async def test_session_search_organizations_integration():
    token_url = "https://aai.openaire.eu/oidc/token"
    expected_url = f"{OPENAIRE_GRAPH_API_BASE_URL}/{EndpointName.ORGANIZATIONS.value}"

    # Mock for the token acquisition
    

    mock_api_response_json = {
        "header": {
            "page": 1,
            "size": 1,
            "numFound": 1,
            "totalPages": 1,
            "maxPage": 1000,
        },
        "results": [
            {
                "id": "org456",
                "legalName": "Searched Org Name",
                "country": {"code": "GR", "name": "Greece"},
            }
        ],
    }
    _params_tso_int = {"countryCode": "GR", "page": "1", "pageSize": "1"}
    auth_strategy = ClientCredentialsAuth(
        client_id="test_id",
        client_secret="test_secret",
        token_url=token_url,
    )
    async with AireloomSession(auth_strategy=auth_strategy) as session:
        filters = OrganizationsFilters(
            countryCode="GR"
        )  # Using countryCode directly for instantiation
        with patch("bibliofabric.client.BaseApiClient._request_with_retry", new_callable=AsyncMock) as mock_request_with_retry:
            mock_response = MagicMock(spec=httpx.Response, status_code=200)
            mock_response.json.return_value = mock_api_response_json
            mock_request_with_retry.return_value = (mock_response, None, 1)
            response = await session.organizations.search(
                filters=filters, page=1, page_size=1
            )
    assert isinstance(response, ApiResponse)
    assert response.results is not None and len(response.results) > 0
    assert isinstance(response.results[0], Organization)
    assert response.results[0].id == "org456"
    assert response.header.numFound == 1


@pytest.mark.asyncio
async def test_session_iterate_organizations_integration():
    token_url = "https://aai.openaire.eu/oidc/token"
    base_url = f"{OPENAIRE_GRAPH_API_BASE_URL}/{EndpointName.ORGANIZATIONS.value}"

    # Mock for the token acquisition
    

    mock_response_page1 = {
        "header": {
            "page": 1,
            "size": 1,
            "numFound": 2,
            "totalPages": 2,
            "nextCursor": "cursor_org1",
        },
        "results": [
            {
                "id": "org_iter1",
                "legalName": "Iter Org 1",
                "country": {"code": "FR", "name": "France"},
            }
        ],
    }
    mock_response_page2 = {
        "header": {
            "page": 2,
            "size": 1,
            "numFound": 2,
            "totalPages": 2,
            "nextCursor": None,
        },
        "results": [
            {
                "id": "org_iter2",
                "legalName": "Iter Org 2",
                "country": {"code": "DE", "name": "Germany"},
            }
        ],
    }
    orgs_iterated = []
    auth_strategy = ClientCredentialsAuth(
        client_id="test_id",
        client_secret="test_secret",
        token_url=token_url,
    )
    async with AireloomSession(auth_strategy=auth_strategy) as session:
        filters = OrganizationsFilters(
            countryCode="EU"
        )  # Using countryCode directly for instantiation
        with patch("bibliofabric.client.BaseApiClient._request_with_retry", new_callable=AsyncMock) as mock_request_with_retry:
            mock_response_page1_obj = MagicMock(spec=httpx.Response, status_code=200)
            mock_response_page1_obj.json.return_value = mock_response_page1
            mock_response_page2_obj = MagicMock(spec=httpx.Response, status_code=200)
            mock_response_page2_obj.json.return_value = mock_response_page2

            mock_request_with_retry.side_effect = [
                (mock_response_page1_obj, None, 1),
                (mock_response_page2_obj, None, 1),
            ]
            async for org in session.organizations.iterate(filters=filters, page_size=1):
                orgs_iterated.append(org)
    assert len(orgs_iterated) == 2
    if len(orgs_iterated) == 2:
        assert isinstance(orgs_iterated[0], Organization)
        assert orgs_iterated[0].id == "org_iter1"
        assert isinstance(orgs_iterated[1], Organization)
        assert orgs_iterated[1].id == "org_iter2"


# --- Projects ---
@pytest.mark.asyncio
async def test_session_get_project_integration():
    token_url = "https://aai.openaire.eu/oidc/token"
    project_id = "proj123"
    expected_url = f"{OPENAIRE_GRAPH_API_BASE_URL}/{EndpointName.PROJECTS.value}"

    # Mock for the token acquisition
    

    mock_api_response_json = {
        "results": [
            {
                "id": project_id,
                "acronym": "MOCKPROJ",
                "code": "FP7-123",
                "title": "Mocked Project Title",
                "fundingTree": [{"id": "fund1", "name": "EC"}],
                "startDate": "2022-01-01",
                "endDate": "2023-01-01",
            }
        ],
        "header": {"numFound": 1, "pageSize": 1},
    }
    auth_strategy = ClientCredentialsAuth(
        client_id="test_id",
        client_secret="test_secret",
        token_url=token_url,
    )
    async with AireloomSession(auth_strategy=auth_strategy) as session:
        with patch("bibliofabric.client.BaseApiClient._request_with_retry", new_callable=AsyncMock) as mock_request_with_retry:
            mock_response = MagicMock(spec=httpx.Response, status_code=200)
            mock_response.json.return_value = mock_api_response_json
            mock_request_with_retry.return_value = (mock_response, None, 1)
            project = await session.projects.get(project_id)
    assert isinstance(project, Project)
    assert project.id == project_id
    assert project.title == "Mocked Project Title"


@pytest.mark.asyncio
async def test_session_search_projects_integration(httpx_mock: HTTPXMock):
    token_url = "https://aai.openaire.eu/oidc/token"
    expected_url = f"{OPENAIRE_GRAPH_API_BASE_URL}/{EndpointName.PROJECTS.value}"

    # Mock for the token acquisition
    

    mock_api_response_json = {
        "header": {
            "page": 1,
            "size": 1,
            "numFound": 1,
            "totalPages": 1,
            "maxPage": 1000,
        },
        "results": [
            {
                "id": "proj456",
                "acronym": "SEARCHPROJ",
                "code": "H2020-456",
                "title": "Searched Project",
                "fundingTree": [{"id": "fund2", "name": "National Funder"}],
                "startDate": "2021-01-01",
                "endDate": "2022-01-01",
            }
        ],
    }
    _params_tsp_int = {"grantID": "H2020", "page": "1", "pageSize": "1"}
    auth_strategy = ClientCredentialsAuth(
        client_id="test_id",
        client_secret="test_secret",
        token_url=token_url,
    )
    async with AireloomSession(auth_strategy=auth_strategy) as session:
        filters = ProjectsFilters(grantID="H2020")
        with patch("bibliofabric.client.BaseApiClient._request_with_retry", new_callable=AsyncMock) as mock_request_with_retry:
            mock_response = MagicMock(spec=httpx.Response, status_code=200)
            mock_response.json.return_value = mock_api_response_json
            mock_request_with_retry.return_value = (mock_response, None, 1)
            response = await session.projects.search(filters=filters, page=1, page_size=1)
    assert isinstance(response, ApiResponse)
    assert response.results is not None and len(response.results) > 0
    assert isinstance(response.results[0], Project)
    assert response.results[0].id == "proj456"
    assert response.header.numFound == 1


@pytest.mark.asyncio
async def test_session_iterate_projects_integration(httpx_mock: HTTPXMock):
    token_url = "https://aai.openaire.eu/oidc/token"
    base_url = f"{OPENAIRE_GRAPH_API_BASE_URL}/{EndpointName.PROJECTS.value}"

    # Mock for the token acquisition
    

    mock_response_page1 = {
        "header": {
            "page": 1,
            "size": 1,
            "numFound": 2,
            "totalPages": 2,
            "nextCursor": "cursor_proj1",
        },
        "results": [
            {
                "id": "proj_iter1",
                "acronym": "ITERPROJ1",
                "code": "FP7-iter1",
                "title": "Iter Project 1",
                "fundingTree": [{"id": "fund_iter1", "name": "EC"}],
                "startDate": "2020-01-01",
                "endDate": "2021-01-01",
            }
        ],
    }
    mock_response_page2 = {
        "header": {
            "page": 2,
            "size": 1,
            "numFound": 2,
            "totalPages": 2,
            "nextCursor": None,
        },
        "results": [
            {
                "id": "proj_iter2",
                "acronym": "ITERPROJ2",
                "code": "H2020-iter2",
                "title": "Iter Project 2",
                "fundingTree": [{"id": "fund_iter2", "name": "ERC"}],
                "startDate": "2019-01-01",
                "endDate": "2020-01-01",
            }
        ],
    }
    projects_iterated = []
    auth_strategy = ClientCredentialsAuth(
        client_id="test_id",
        client_secret="test_secret",
        token_url=token_url,
    )
    async with AireloomSession(auth_strategy=auth_strategy) as session:
        filters = ProjectsFilters(fundingStreamId="EC")
        with patch("bibliofabric.client.BaseApiClient._request_with_retry", new_callable=AsyncMock) as mock_request_with_retry:
            mock_response_page1_obj = MagicMock(spec=httpx.Response, status_code=200)
            mock_response_page1_obj.json.return_value = mock_response_page1
            mock_response_page2_obj = MagicMock(spec=httpx.Response, status_code=200)
            mock_response_page2_obj.json.return_value = mock_response_page2

            mock_request_with_retry.side_effect = [
                (mock_response_page1_obj, None, 1),
                (mock_response_page2_obj, None, 1),
            ]
            async for project in session.projects.iterate(filters=filters, page_size=1):
                projects_iterated.append(project)
    assert len(projects_iterated) == 2
    if len(projects_iterated) == 2:
        assert isinstance(projects_iterated[0], Project)
        assert projects_iterated[0].id == "proj_iter1"
        assert isinstance(projects_iterated[1], Project)
        assert projects_iterated[1].id == "proj_iter2"


# --- DataSources ---
@pytest.mark.asyncio
async def test_session_get_data_source_integration(httpx_mock: HTTPXMock):
    token_url = "https://aai.openaire.eu/oidc/token"
    ds_id = "ds123"
    expected_url = f"{OPENAIRE_GRAPH_API_BASE_URL}/{EndpointName.DATA_SOURCES.value}"

    # Mock for the token acquisition
    

    mock_api_response_json = {
        "results": [
            {
                "id": ds_id,
                "officialName": "Mocked Data Source",
                "englishName": "Mocked Data Source EN",
                "websiteUrl": "http://example.com/ds",
                "type": {"name": "repository"},
            }
        ],
        "header": {"numFound": 1, "pageSize": 1},
    }
    auth_strategy = ClientCredentialsAuth(
        client_id="test_id",
        client_secret="test_secret",
        token_url=token_url,
    )
    async with AireloomSession(auth_strategy=auth_strategy) as session:
        with patch("bibliofabric.client.BaseApiClient._request_with_retry", new_callable=AsyncMock) as mock_request_with_retry:
            mock_response = MagicMock(spec=httpx.Response, status_code=200)
            mock_response.json.return_value = mock_api_response_json
            mock_request_with_retry.return_value = (mock_response, None, 1)
            data_source = await session.data_sources.get(ds_id)
    assert isinstance(data_source, DataSource)
    assert data_source.id == ds_id
    assert data_source.officialName == "Mocked Data Source"


@pytest.mark.asyncio
async def test_session_search_data_sources_integration(httpx_mock: HTTPXMock):
    token_url = "https://aai.openaire.eu/oidc/token"
    expected_url = f"{OPENAIRE_GRAPH_API_BASE_URL}/{EndpointName.DATA_SOURCES.value}"

    # Mock for the token acquisition
    

    mock_api_response_json = {
        "header": {
            "page": 1,
            "size": 1,
            "numFound": 1,
            "totalPages": 1,
            "maxPage": 1000,
        },
        "results": [
            {
                "id": "ds456",
                "officialName": "Searched Data Source",
                "englishName": "Searched Data Source EN",
                "websiteUrl": "http://example.com/ds_search",
                "type": {"name": "journal"},
            }
        ],
    }
    _params_tsds_int = {
        "openaireCompatibility": "UNKNOWN",
        "page": "1",
        "pageSize": "1",
    }
    auth_strategy = ClientCredentialsAuth(
        client_id="test_id",
        client_secret="test_secret",
        token_url=token_url,
    )
    async with AireloomSession(auth_strategy=auth_strategy) as session:
        filters = DataSourcesFilters(openaireCompatibility="UNKNOWN")
        with patch("bibliofabric.client.BaseApiClient._request_with_retry", new_callable=AsyncMock) as mock_request_with_retry:
            mock_response = MagicMock(spec=httpx.Response, status_code=200)
            mock_response.json.return_value = mock_api_response_json
            mock_request_with_retry.return_value = (mock_response, None, 1)
            response = await session.data_sources.search(
                filters=filters, page=1, page_size=1
            )
    assert isinstance(response, ApiResponse)
    assert response.results is not None and len(response.results) > 0
    assert isinstance(response.results[0], DataSource)
    assert response.results[0].id == "ds456"
    assert response.header.numFound == 1


@pytest.mark.asyncio
async def test_session_iterate_data_sources_integration(httpx_mock: HTTPXMock):
    token_url = "https://aai.openaire.eu/oidc/token"
    base_url = f"{OPENAIRE_GRAPH_API_BASE_URL}/{EndpointName.DATA_SOURCES.value}"

    # Mock for the token acquisition
    

    mock_response_page1 = {
        "header": {
            "page": 1,
            "size": 1,
            "numFound": 2,
            "totalPages": 2,
            "nextCursor": "cursor_ds1",
        },
        "results": [
            {
                "id": "ds_iter1",
                "officialName": "Iter DS 1",
                "englishName": "Iter DS 1 EN",
                "websiteUrl": "http://example.com/ds_iter1",
                "type": {"name": "aggregator"},
            }
        ],
    }
    mock_response_page2 = {
        "header": {
            "page": 2,
            "size": 1,
            "numFound": 2,
            "totalPages": 2,
            "nextCursor": None,
        },
        "results": [
            {
                "id": "ds_iter2",
                "officialName": "Iter DS 2",
                "englishName": "Iter DS 2 EN",
                "websiteUrl": "http://example.com/ds_iter2",
                "type": {"name": "repository"},
            }
        ],
    }
    ds_iterated = []
    auth_strategy = ClientCredentialsAuth(
        client_id="test_id",
        client_secret="test_secret",
        token_url=token_url,
    )
    async with AireloomSession(auth_strategy=auth_strategy) as session:
        filters = DataSourcesFilters()  # No countryCode
        with patch("bibliofabric.client.BaseApiClient._request_with_retry", new_callable=AsyncMock) as mock_request_with_retry:
            mock_response_page1_obj = MagicMock(spec=httpx.Response, status_code=200)
            mock_response_page1_obj.json.return_value = mock_response_page1
            mock_response_page2_obj = MagicMock(spec=httpx.Response, status_code=200)
            mock_response_page2_obj.json.return_value = mock_response_page2

            mock_request_with_retry.side_effect = [
                (mock_response_page1_obj, None, 1),
                (mock_response_page2_obj, None, 1),
            ]
            async for ds in session.data_sources.iterate(filters=filters, page_size=1):
                ds_iterated.append(ds)
    assert len(ds_iterated) == 2
    if len(ds_iterated) == 2:
        assert isinstance(ds_iterated[0], DataSource)
        assert ds_iterated[0].id == "ds_iter1"
        assert isinstance(ds_iterated[1], DataSource)
        assert ds_iterated[1].id == "ds_iter2"


# --- Scholix ---
@pytest.mark.asyncio
async def test_session_search_scholix_integration(httpx_mock: HTTPXMock):
    token_url = "https://aai.openaire.eu/oidc/token"
    source_pid = "10.1234/source"
    expected_url = f"{OPENAIRE_SCHOLIX_API_BASE_URL}/{EndpointName.SCHOLIX.value}"

    # Mock for the token acquisition
    

    mock_api_response_json = {
        "currentPage": 0,
        "totalLinks": 1,
        "totalPages": 1,
        "result": [
            {
                "LinkProvider": [{"Name": "Mock Provider"}],
                "LinkPublicationDate": "2023-01-01T00:00:00Z",
                "RelationshipType": {"Name": "References"},
                "Source": {
                    "Identifier": [{"ID": source_pid, "IDScheme": "doi"}],
                    "Type": "publication",
                },
                "Target": {
                    "Identifier": [{"ID": "10.5678/target", "IDScheme": "doi"}],
                    "Type": "dataset",
                },
            }
        ],
    }
    _params_tss_int = {"sourcePid": source_pid, "page": "0", "rows": "1"}
    auth_strategy = ClientCredentialsAuth(
        client_id="test_id",
        client_secret="test_secret",
        token_url=token_url,
    )
    async with AireloomSession(auth_strategy=auth_strategy) as session:
        filters = ScholixFilters(sourcePid=source_pid)
        with patch("bibliofabric.client.BaseApiClient._request_with_retry", new_callable=AsyncMock) as mock_request_with_retry:
            mock_response = MagicMock(spec=httpx.Response, status_code=200)
            mock_response.json.return_value = mock_api_response_json
            mock_request_with_retry.return_value = (mock_response, None, 1)
            response: ScholixResponse = await session.scholix.search_links(
                filters=filters, page=0, page_size=1
            )
    assert isinstance(response, ScholixResponse)
    assert response.result is not None and len(response.result) > 0
    assert isinstance(response.result[0], ScholixLink)
    assert response.result[0].source.identifier[0].id_val == source_pid
    assert response.total_links == 1


@pytest.mark.asyncio
async def test_session_iterate_scholix_integration(httpx_mock: HTTPXMock):
    token_url = "https://aai.openaire.eu/oidc/token"
    source_pid = "10.9876/iter_source"
    base_url = f"{OPENAIRE_SCHOLIX_API_BASE_URL}/{EndpointName.SCHOLIX.value}"

    # Mock for the token acquisition
    

    mock_response_page0 = {
        "currentPage": 0,
        "totalLinks": 2,
        "totalPages": 2,
        "result": [
            {
                "LinkProvider": [{"Name": "Iter Provider 1"}],
                "LinkPublicationDate": "2023-02-01T00:00:00Z",
                "RelationshipType": {"Name": "IsReferencedBy"},
                "Source": {
                    "Identifier": [{"ID": source_pid, "IDScheme": "doi"}],
                    "Type": "software",
                },
                "Target": {
                    "Identifier": [{"ID": "target1", "IDScheme": "other"}],
                    "Type": "other",
                },
            }
        ],
    }
    mock_response_page1 = {
        "currentPage": 1,
        "totalLinks": 2,
        "totalPages": 2,
        "result": [
            {
                "LinkProvider": [{"Name": "Iter Provider 2"}],
                "LinkPublicationDate": "2023-02-02T00:00:00Z",
                "RelationshipType": {"Name": "IsSupplementTo"},
                "Source": {
                    "Identifier": [{"ID": source_pid, "IDScheme": "doi"}],
                    "Type": "software",
                },
                "Target": {
                    "Identifier": [{"ID": "target2", "IDScheme": "other"}],
                    "Type": "other",
                },
            }
        ],
    }
    links_iterated = []
    auth_strategy = ClientCredentialsAuth(
        client_id="test_id",
        client_secret="test_secret",
        token_url=token_url,
    )
    async with AireloomSession(auth_strategy=auth_strategy) as session:
        filters = ScholixFilters(sourcePid=source_pid)
        with patch("bibliofabric.client.BaseApiClient._request_with_retry", new_callable=AsyncMock) as mock_request_with_retry:
            mock_response_page0_obj = MagicMock(spec=httpx.Response, status_code=200)
            mock_response_page0_obj.json.return_value = mock_response_page0
            mock_response_page1_obj = MagicMock(spec=httpx.Response, status_code=200)
            mock_response_page1_obj.json.return_value = mock_response_page1

            mock_request_with_retry.side_effect = [
                (mock_response_page0_obj, None, 1),
                (mock_response_page1_obj, None, 1),
            ]
            async for link_item in session.scholix.iterate_links(
                filters=filters, page_size=5
            ):
                links_iterated.append(link_item)
    assert len(links_iterated) == 2
    if len(links_iterated) == 2:
        assert isinstance(links_iterated[0], ScholixLink)
        assert (
            links_iterated[0].link_provider is not None
            and links_iterated[0].link_provider[0].name == "Iter Provider 1"
        )
        assert isinstance(links_iterated[1], ScholixLink)
        assert (
            links_iterated[1].link_provider is not None
            and links_iterated[1].link_provider[0].name == "Iter Provider 2"
        )


# --- Legacy Test Stubs (to be removed or integrated if still relevant) ---
@pytest.mark.asyncio
async def test_get_research_product_success(httpx_mock: HTTPXMock):
    token_url = "https://aai.openaire.eu/oidc/token"
    product_id = "oai:zenodo.org:7668094"

    # Mock for the token acquisition
    httpx_mock.add_response(
        method="POST",
        url=token_url,
        json={"access_token": "mock_token", "expires_in": 3600},
        status_code=200,
    )

    mock_product_response = {
        "id": product_id,
        "title": "Mocked Test Product Title",
        "type": "publication",
        "publicationDate": "2023-01-01",
    }
    httpx_mock.add_response(
        url=f"{OPENAIRE_GRAPH_API_BASE_URL}/researchProducts?id={product_id}&pageSize=1",
        method="GET",
        json={
            "results": [mock_product_response],
            "header": {"numFound": 1, "pageSize": 1},
        },
        status_code=200,
    )
    auth_strategy = ClientCredentialsAuth(
        client_id="test_id",
        client_secret="test_secret",
        token_url=token_url,
    )
    async with AireloomSession(auth_strategy=auth_strategy) as session:
        # Removed the patch for _request_with_retry as httpx_mock should handle the response
        product = await session.research_products.get(product_id)
        assert product is not None
        assert product.id == product_id
        assert isinstance(product.title, str)


@pytest.mark.asyncio
async def test_get_research_product_not_found(httpx_mock: HTTPXMock):
    token_url = "https://aai.openaire.eu/oidc/token"
    product_id = "nonexistent:id_123456789_invalid"

    # Mock for the token acquisition
    httpx_mock.add_response(
        method="POST",
        url=token_url,
        json={"access_token": "mock_token", "expires_in": 3600},
        status_code=200,
    )

    httpx_mock.add_response(
        url=f"{OPENAIRE_GRAPH_API_BASE_URL}/researchProducts?id={product_id}&pageSize=1",
        method="GET",
        status_code=404,
        json={"message": "Not Found"},
    )
    auth_strategy = ClientCredentialsAuth(
        client_id="test_id",
        client_secret="test_secret",
        token_url=token_url,
    )
    async with AireloomSession(auth_strategy=auth_strategy) as session:
        with pytest.raises(
            BibliofabricError, match="API request failed with status 404"
        ):
            await session.research_products.get(product_id)


@pytest.mark.asyncio
async def test_search_research_products_simple(httpx_mock: HTTPXMock):
    token_url = "https://aai.openaire.eu/oidc/token"

    # Mock for the token acquisition
    httpx_mock.add_response(
        method="POST",
        url=token_url,
        json={"access_token": "mock_token", "expires_in": 3600},
        status_code=200,
    )

    mock_api_response_json = {
        "header": {
            "page": 1,
            "size": 5,
            "numFound": 1,
            "totalPages": 1,
        },  # Use numFound
        "results": [
            {
                "id": "rp_search_legacy",
                "title": "Legacy Search Product",
                "type": "publication",
                "publicationDate": "2023-04-01",
            }
        ],
    }
    _params_tsrps = {"mainTitle": "Open Science", "pageSize": "5", "page": "1"}
    httpx_mock.add_response(
        url=f"{OPENAIRE_GRAPH_API_BASE_URL}/researchProducts?{urllib.parse.urlencode(_params_tsrps)}",
        method="GET",
        json=mock_api_response_json,
    )
    auth_strategy = ClientCredentialsAuth(
        client_id="test_id",
        client_secret="test_secret",
        token_url=token_url,
    )
    async with AireloomSession(auth_strategy=auth_strategy) as session:
        filters = ResearchProductsFilters(mainTitle="Open Science")
        response = await session.research_products.search(
            filters=filters, page_size=5, page=1
        )
        assert response is not None
        assert response.results is not None and len(response.results) <= 5
        if response.results:
            assert isinstance(response.results[0].id, str)
            assert isinstance(response.results[0].title, str)


@pytest.mark.asyncio
async def test_iterate_research_products(httpx_mock: HTTPXMock):
    token_url = "https://aai.openaire.eu/oidc/token"
    base_url = f"{OPENAIRE_GRAPH_API_BASE_URL}/researchProducts"

    # Mock for the token acquisition
    httpx_mock.add_response(
        method="POST",
        url=token_url,
        json={"access_token": "mock_token", "expires_in": 3600},
        status_code=200,
    )

    mock_response_page1 = {
        "header": {
            "numFound": 2,
            "nextCursor": "cursor_legacy1",
            "size": 1,
            "page": 1,
        },  # Use numFound
        "results": [
            {
                "id": "id_legacy1",
                "title": "Title Legacy 1",
                "type": "dataset",
                "publicationDate": "2023-01-01",
            }
        ],
    }
    mock_response_page2 = {
        "header": {
            "numFound": 2,
            "nextCursor": None,
            "size": 1,
            "page": 2,
        },  # Use numFound
        "results": [
            {
                "id": "id_legacy2",
                "title": "Title Legacy 2",
                "type": "software",
                "publicationDate": "2023-01-02",
            }
        ],
    }
    _params_tirp_1 = {"mainTitle": "FAIR data", "pageSize": "1", "cursor": "*"}
    httpx_mock.add_response(
        url=f"{base_url}?{urllib.parse.urlencode(_params_tirp_1)}",
        method="GET",
        json=mock_response_page1,
    )
    _params_tirp_2 = {
        "mainTitle": "FAIR data",
        "pageSize": "1",
        "cursor": "cursor_legacy1",
    }
    httpx_mock.add_response(
        url=f"{base_url}?{urllib.parse.urlencode(_params_tirp_2)}",
        method="GET",
        json=mock_response_page2,
    )
    auth_strategy = ClientCredentialsAuth(
        client_id="test_id",
        client_secret="test_secret",
        token_url=token_url,
    )
    async with AireloomSession(auth_strategy=auth_strategy) as session:
        count = 0
        max_items_to_iterate = 2
        filters = ResearchProductsFilters(mainTitle="FAIR data")
        async for product in session.research_products.iterate(
            filters=filters, page_size=1
        ):
            assert product is not None
            assert isinstance(product.id, str)
            count += 1
            if count >= max_items_to_iterate:
                break
        assert count == max_items_to_iterate


@pytest.mark.asyncio
async def test_search_scholix_links_success(httpx_mock: HTTPXMock):
    token_url = "https://aai.openaire.eu/oidc/token"

    # Mock for the token acquisition
    httpx_mock.add_response(
        method="POST",
        url=token_url,
        json={"access_token": "mock_token", "expires_in": 3600},
        status_code=200,
    )

    httpx_mock.add_response(
        url=f"{OPENAIRE_SCHOLIX_API_BASE_URL}/Links?sourcePid={KNOWN_DOI_WITH_LINKS}&page=0&rows=10",
        method="GET",
        json=MOCK_SCHOLIX_RESPONSE,
        status_code=200,
    )
    auth_strategy = ClientCredentialsAuth(
        client_id="test_id",
        client_secret="test_secret",
        token_url=token_url,
    )
    async with AireloomSession(auth_strategy=auth_strategy) as session:
        filters = ScholixFilters(sourcePid=KNOWN_DOI_WITH_LINKS)
        response: ScholixResponse = await session.scholix.search_links(
            filters=filters, page_size=10, page=0
        )
        assert response is not None
        assert response.current_page == 0
        assert response.total_links >= 0
        assert response.result is not None
        assert 0 <= len(response.result) <= 10
        if response.result:
            link = response.result[0]
            assert link.source is not None
            assert link.target is not None
            assert isinstance(link.source.identifier, list)
            assert isinstance(link.target.identifier, list)
            assert link.relationship_type is not None


@pytest.mark.asyncio
async def test_iterate_scholix_links(httpx_mock: HTTPXMock):
    token_url = "https://aai.openaire.eu/oidc/token"

    # Mock for the token acquisition
    httpx_mock.add_response(
        method="POST",
        url=token_url,
        json={"access_token": "mock_token", "expires_in": 3600},
        status_code=200,
    )

    mock_response_page1 = MOCK_SCHOLIX_RESPONSE.copy()
    mock_response_page1["currentPage"] = 0
    mock_response_page1["totalLinks"] = 7
    mock_response_page1["totalPages"] = 2
    base_link = MOCK_SCHOLIX_RESPONSE["result"][0]
    mock_response_page1["result"] = []
    for i in range(5):
        link = base_link.copy()
        link["LinkPublicationDate"] = f"2023-01-15T12:00:0{i}Z"
        link["Source"] = {
            "Identifier": [{"ID": f"{KNOWN_DOI_WITH_LINKS}/{i}", "IDScheme": "doi"}],
            "Type": "publication",
        }
        link["Target"] = {
            "Identifier": [{"ID": f"10.1234/target.dataset.{i}", "IDScheme": "doi"}],
            "Type": "dataset",
        }
        link["RelationshipType"]["SubTypeSchema"] = (
            "http://example.com/datacite"  # Ensure valid URL
        )
        mock_response_page1["result"].append(link)

    httpx_mock.add_response(
        url=f"{OPENAIRE_SCHOLIX_API_BASE_URL}/Links?sourcePid={KNOWN_DOI_WITH_LINKS}&page=0&rows=5",
        method="GET",
        json=mock_response_page1,
        status_code=200,
    )

    mock_response_page2 = MOCK_SCHOLIX_RESPONSE.copy()
    mock_response_page2["currentPage"] = 1
    mock_response_page2["totalLinks"] = 7
    mock_response_page2["totalPages"] = 2
    mock_response_page2["result"] = []
    for i in range(2):
        link = base_link.copy()
        link["LinkPublicationDate"] = f"2023-01-16T13:00:0{i}Z"
        link["Source"] = {
            "Identifier": [
                {"ID": f"{KNOWN_DOI_WITH_LINKS}/{i + 5}", "IDScheme": "doi"}
            ],
            "Type": "publication",
        }
        link["Target"] = {
            "Identifier": [
                {"ID": f"10.1234/target.dataset.{i + 5}", "IDScheme": "doi"}
            ],
            "Type": "dataset",
        }
        link["RelationshipType"]["SubTypeSchema"] = (
            "http://example.com/datacite"  # Ensure valid URL
        )
        mock_response_page2["result"].append(link)

    httpx_mock.add_response(
        url=f"{OPENAIRE_SCHOLIX_API_BASE_URL}/Links?sourcePid={KNOWN_DOI_WITH_LINKS}&page=1&rows=5",
        method="GET",
        json=mock_response_page2,
        status_code=200,
    )
    auth_strategy = ClientCredentialsAuth(
        client_id="test_id",
        client_secret="test_secret",
        token_url=token_url,
    )
    async with AireloomSession(auth_strategy=auth_strategy) as session:
        count = 0
        max_items_to_iterate = 7
        filters = ScholixFilters(sourcePid=KNOWN_DOI_WITH_LINKS)
        async for link_item in session.scholix.iterate_links(
            filters=filters, page_size=5
        ):
            assert link_item is not None
            assert link_item.relationship_type is not None
            assert link_item.source is not None
            assert link_item.target is not None
            assert link_item.link_publication_date is not None
            count += 1
            if count >= max_items_to_iterate:
                break
        assert count == max_items_to_iterate


from pydantic import ValidationError


@pytest.mark.asyncio
async def test_search_scholix_ignored_invalid_filter_key(httpx_mock: HTTPXMock):
    """Test that providing an invalid filter key to ScholixFilters raises a ValidationError."""
    source_pid = KNOWN_DOI_WITH_LINKS
    # expected_url = f"{OPENAIRE_SCHOLIX_API_BASE_URL}/{EndpointName.SCHOLIX.value}" # Not needed as API call won't happen

    # mocked_api_response_for_test = MOCK_SCHOLIX_RESPONSE.copy() # Not needed

    # httpx_mock.add_response( # Not needed as API call won't happen
    #     url=expected_url,
    #     method="GET",
    #     json=mocked_api_response_for_test,
    #     params={"sourcePid": source_pid, "page": "0", "rows": "10"},
    # )

    # async with AireloomSession() as session: # Session not needed for this check
    with pytest.raises(ValidationError) as excinfo:
        ScholixFilters(sourcePid=source_pid, someMadeUpFilterKey="someValue")  # type: ignore[call-arg]

    assert "someMadeUpFilterKey" in str(excinfo.value)
    assert "Extra inputs are not permitted" in str(
        excinfo.value
    )  # Pydantic v2 error message for extra fields

    # The following lines are not reachable if ValidationError is raised as expected.
    # response: ScholixResponse = await session.scholix.search_links(
    #     filters=filters_with_extra, page_size=10, page=0
    # )

    # assert response is not None
    # assert response.total_links == mocked_api_response_for_test["totalLinks"]
    # if response.result:
    #     assert len(response.result) == len(mocked_api_response_for_test["result"])
