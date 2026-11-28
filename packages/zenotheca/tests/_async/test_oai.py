"""Outgoing request shape, fixture parsing, and error mapping for OAI-PMH."""

import pytest
from zenotheca import ConfigurationError, NotFoundError

from ..conftest import load_text


async def test_identify_parses_the_fixture(client, httpx_mock):
    httpx_mock.add_response(
        text=(
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">'
            "<responseDate>2026-11-27T22:44:00Z</responseDate>"
            '<request verb="Identify">https://zenodo.org/oai2d</request>'
            "<Identify>"
            "<repositoryName>Zenodo</repositoryName>"
            "<baseURL>https://zenodo.org/oai2d</baseURL>"
            "<protocolVersion>2.0</protocolVersion>"
            "<earliestDatestamp>2013-11-01T00:00:00Z</earliestDatestamp>"
            "<deletedRecord>persistent</deletedRecord>"
            "<granularity>seconds</granularity>"
            "<adminEmail>info@zenodo.org</adminEmail>"
            "</Identify>"
            "</OAI-PMH>"
        )
    )
    answer = await client.oai.identify()
    request = httpx_mock.get_requests()[-1]
    assert request.url.host == "zenodo.org"
    assert str(request.url) == "https://zenodo.org/oai2d?verb=Identify"
    assert answer.identify is not None
    assert answer.identify.repository_name == "Zenodo"
    assert answer.identify.granularity == "seconds"
    assert answer.response_date is not None


async def test_list_metadata_formats_parses_prefixes(client, httpx_mock):
    httpx_mock.add_response(text=load_text("oai_metadata_formats.xml"))
    formats = await client.oai.list_metadata_formats()
    request = httpx_mock.get_requests()[-1]
    assert request.url.params["verb"] == "ListMetadataFormats"
    prefixes = [item.metadata_prefix for item in formats.formats]
    assert "oai_dc" in prefixes
    assert "marcxml" in prefixes


async def test_list_sets_pages_follow_tokens(client, httpx_mock):
    httpx_mock.add_response(text=load_text("oai_sets_page1.xml"))
    httpx_mock.add_response(text=load_text("oai_sets_page2.xml"))
    page_one = await client.oai.list_sets()
    token = page_one.resumption_token
    assert token is not None and token.token
    assert token.complete_list_size == 48294
    assert token.cursor == 0
    page_two = await client.oai.list_sets(resumption_token=token.token)
    second = httpx_mock.get_requests()[-1]
    assert second.url.params["resumptionToken"] == token.token
    assert page_two.response_date is not None


async def test_list_records_parses_raw_metadata(client, httpx_mock):
    httpx_mock.add_response(text=load_text("oai_records_page1.xml"))
    page = await client.oai.list_records("oai_datacite4", from_="2026-11-20")
    request = httpx_mock.get_requests()[-1]
    assert request.url.params["verb"] == "ListRecords"
    assert request.url.params["metadataPrefix"] == "oai_datacite4"
    assert request.url.params["from"] == "2026-11-20"
    record = page.records[0]
    assert record.header is not None
    assert record.header.identifier.startswith("oai:zenodo.org:")
    assert record.metadata is not None and record.metadata.startswith("<")
    assert page.resumption_token is not None


async def test_list_identifiers_parses_headers(client, httpx_mock):
    httpx_mock.add_response(text=load_text("oai_identifiers_page1.xml"))
    page = await client.oai.list_identifiers(
        "oai_dc", from_="2026-11-20", until="2026-11-26"
    )
    request = httpx_mock.get_requests()[-1]
    assert request.url.params["until"] == "2026-11-26"
    assert page.headers
    assert page.headers[0].datestamp


async def test_get_record_parses_header_and_metadata(client, httpx_mock):
    httpx_mock.add_response(text=load_text("oai_get_record.xml"))
    answer = await client.oai.get_record("oai:zenodo.org:24378467", "oai_dc")
    request = httpx_mock.get_requests()[-1]
    assert request.url.params["verb"] == "GetRecord"
    assert request.url.params["identifier"] == "oai:zenodo.org:24378467"
    assert answer.record is not None
    assert answer.record.header is not None
    assert answer.record.metadata_namespace == (
        "http://www.openarchives.org/OAI/2.0/oai_dc/"
    )


async def test_no_records_match_answers_an_empty_page(client, httpx_mock):
    httpx_mock.add_response(status_code=422, text=load_text("oai_no_records_match.xml"))
    page = await client.oai.list_records("oai_dc", set="user-ror-data")
    request = httpx_mock.get_requests()[-1]
    assert request.url.params["set"] == "user-ror-data"
    assert page.records == []


async def test_iterate_records_follows_resumption_tokens(client, httpx_mock):
    httpx_mock.add_response(text=load_text("oai_records_page1.xml"))
    httpx_mock.add_response(text=load_text("oai_no_records_match.xml"))
    records = [record async for record in client.oai.iterate_records("oai_datacite4")]
    assert len(records) == 1
    second = httpx_mock.get_requests()[-1]
    assert second.url.params["resumptionToken"]


async def test_iterate_identifiers_follows_resumption_tokens(client, httpx_mock):
    httpx_mock.add_response(text=load_text("oai_identifiers_page1.xml"))
    httpx_mock.add_response(text=load_text("oai_no_records_match.xml"))
    headers = [header async for header in client.oai.iterate_identifiers("oai_dc")]
    assert len(headers) == 1


async def test_id_does_not_exist_maps_to_not_found(client, httpx_mock):
    httpx_mock.add_response(
        status_code=422,
        text=(
            '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">'
            '<request verb="GetRecord">https://zenodo.org/oai2d</request>'
            '<error code="idDoesNotExist">No matching identifier</error>'
            "</OAI-PMH>"
        ),
    )
    with pytest.raises(NotFoundError):
        await client.oai.get_record("oai:zenodo.org:1", "oai_dc")


async def test_bad_argument_maps_to_configuration_error(client, httpx_mock):
    httpx_mock.add_response(
        status_code=422,
        text=(
            '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">'
            '<request verb="ListRecords">https://zenodo.org/oai2d</request>'
            '<error code="badArgument">The from value is invalid</error>'
            "</OAI-PMH>"
        ),
    )
    with pytest.raises(ConfigurationError):
        await client.oai.list_records("oai_dc", from_="not-a-date")


async def test_bad_resumption_token_maps_to_configuration_error(client, httpx_mock):
    httpx_mock.add_response(
        status_code=422,
        text=(
            '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">'
            '<request verb="ListRecords">https://zenodo.org/oai2d</request>'
            '<error code="badResumptionToken">Invalid token</error>'
            "</OAI-PMH>"
        ),
    )
    with pytest.raises(ConfigurationError):
        await client.oai.list_records("oai_dc", resumption_token="stale")


async def test_empty_arguments_raise_without_request(client, httpx_mock):
    with pytest.raises(ConfigurationError):
        await client.oai.list_records("  ")
    with pytest.raises(ConfigurationError):
        await client.oai.get_record("oai:zenodo.org:1", " ")
    assert httpx_mock.get_requests() == []


async def test_no_set_hierarchy_answers_empty_sets(client, httpx_mock):
    httpx_mock.add_response(
        status_code=422,
        text=(
            '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">'
            '<request verb="ListSets">https://zenodo.org/oai2d</request>'
            '<error code="noSetHierarchy">No sets</error>'
            "</OAI-PMH>"
        ),
    )
    page = await client.oai.list_sets()
    assert page.sets == []
