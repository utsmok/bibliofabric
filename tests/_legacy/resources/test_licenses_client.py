"""Tests for LicensesClient (list/iterate only — no single-item route upstream)."""

import pytest

from stavrophora.models import License
from stavrophora.resources.licenses_client import LicensesClient

from .conftest import _mock_response

LICENSE = {"URL": "https://creativecommons.org/licenses/by/4.0/", "work-count": 100}


@pytest.fixture
def licenses_client(mock_api_client):
    return LicensesClient(mock_api_client)


@pytest.mark.asyncio
async def test_search_licenses(licenses_client, mock_api_client):
    mock_api_client.request.return_value = _mock_response(
        {"message": {"total-results": 1, "items": [LICENSE]}}
    )
    response = await licenses_client.search(page_size=10)
    license_item = response.message.items[0]
    assert isinstance(license_item, License)
    assert license_item.work_count == 100
    assert license_item.url.endswith("/by/4.0/")


def test_no_single_item_route():
    """Crossref serves no /licenses/{id} route; the client must not offer get."""
    assert not hasattr(LicensesClient, "get")
