"""The proxy's redirect listing (``?action=showurls``): request shape and parsing."""

import pytest
from bibliofabric.exceptions import ConfigurationError, NotFoundError, ValidationError

from ..conftest import load_fixture

XML_HEADERS = {"content-type": "text/xml;charset=utf-8"}


def last_request(httpx_mock):
    return httpx_mock.get_requests()[-1]


async def test_locations_of_a_crossref_doi(client, httpx_mock):
    httpx_mock.add_response(
        text=load_fixture("showurls_crossref.xml"), headers=XML_HEADERS
    )
    locations = await client.locations("10.1038/nature12373")
    assert len(locations) == 2
    landing, metadata = locations
    assert landing.href == "https://www.nature.com/articles/nature12373"
    assert landing.mode == "legacy"
    assert landing.weight == "1.0"
    assert landing.http_role is None
    assert metadata.http_role == "conneg"
    assert metadata.weight == "0"
    assert metadata.href == (
        "https://api.crossref.org/v1/works/10.1038%2Fnature12373/transform"
    )
    assert metadata.href_template == "https://api.crossref.org/v1/works/{hdl}/transform"


async def test_locations_of_a_datacite_doi(client, httpx_mock):
    httpx_mock.add_response(
        text=load_fixture("showurls_datacite.xml"), headers=XML_HEADERS
    )
    metadata = (await client.locations("https://doi.org/10.5281/zenodo.1238808"))[1]
    assert metadata.href == "https://data.crosscite.org/10.5281%2Fzenodo.1238808"
    assert metadata.href_template == "https://data.crosscite.org/{hdl}"


async def test_locations_of_a_doi_without_a_metadata_server(client, httpx_mock):
    httpx_mock.add_response(text=load_fixture("showurls_demo.xml"), headers=XML_HEADERS)
    locations = await client.locations("10.1000/202")
    assert [location.href for location in locations] == [
        "http://www.doi.org/doi_handbook/1_Introduction.html#1.6"
    ]


async def test_locations_request_shape(client, httpx_mock):
    httpx_mock.add_response(text="<locations />", headers=XML_HEADERS)
    assert await client.locations("doi:10.1000/res#test") == []
    request = last_request(httpx_mock)
    assert request.method == "GET"
    assert request.url.raw_path == b"/10.1000/res%23test?action=showurls"


async def test_locations_keep_every_attribute(client, httpx_mock):
    httpx_mock.add_response(
        text=(
            '<locations><location href="https://a.example/x" country="us" '
            'datacenter="dc1"/></locations>'
        ),
        headers=XML_HEADERS,
    )
    location = (await client.locations("10.1000/1"))[0]
    assert location.model_extra == {"country": "us", "datacenter": "dc1"}


async def test_locations_unknown_doi_raises_not_found(client, httpx_mock):
    httpx_mock.add_response(
        text="<!DOCTYPE html><html><title>Error: DOI Not Found</title></html>",
        status_code=404,
        headers={"content-type": "text/html"},
    )
    with pytest.raises(NotFoundError):
        await client.locations("10.9999/nope")


async def test_locations_rejects_a_malformed_doi_before_sending(client, httpx_mock):
    with pytest.raises(ConfigurationError, match="Not a DOI name"):
        await client.locations("nonsense")
    assert not httpx_mock.get_requests()


async def test_locations_of_a_body_that_is_not_the_listing_raise(client, httpx_mock):
    httpx_mock.add_response(text="<html><body>nope</body></html>", headers=XML_HEADERS)
    with pytest.raises(ConfigurationError, match="root 'html'"):
        await client.locations("10.1038/nature12373")


async def test_locations_of_malformed_xml_raise(client, httpx_mock):
    httpx_mock.add_response(
        text="<locations><location></locations>", headers=XML_HEADERS
    )
    with pytest.raises(ConfigurationError, match="well-formed"):
        await client.locations("10.1038/nature12373")


async def test_locations_of_a_location_without_href_raise(client, httpx_mock):
    httpx_mock.add_response(
        text='<locations><location weight="1.0"/></locations>', headers=XML_HEADERS
    )
    with pytest.raises(ValidationError, match="RedirectLocation"):
        await client.locations("10.1038/nature12373")
