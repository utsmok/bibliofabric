"""Outgoing request shape: paths, params, filter syntax, paging, guards."""

import pytest
from rorifer import (
    ConfigurationError,
    NotFoundError,
    OrganizationFilters,
    RoriferClient,
)

from ..conftest import envelope, load_fixture, organization

ORGANIZATION = load_fixture("organization.json")
PAGE = load_fixture("search_page.json")
ERRORS_FILTER = load_fixture("errors_filter.json")
ERRORS_PAGE = load_fixture("errors_page.json")
NOT_FOUND = load_fixture("notfound.json")


def last_request(httpx_mock):
    return httpx_mock.get_requests()[-1]


def last_params(httpx_mock) -> dict[str, str]:
    return dict(last_request(httpx_mock).url.params)


async def test_get_uses_bare_ror_id_and_accepts_json(client, httpx_mock):
    httpx_mock.add_response(json=ORGANIZATION)
    record = await client.organizations.get("https://ror.org/006HF6230")
    assert record.id == ORGANIZATION["id"]
    request = last_request(httpx_mock)
    assert request.url.path == "/v2/organizations/006hf6230"
    assert request.headers["accept"] == "application/json"


async def test_get_raises_not_found(client, httpx_mock):
    httpx_mock.add_response(json=NOT_FOUND, status_code=404)
    with pytest.raises(NotFoundError) as error:
        await client.organizations.get("00yjdzt39")
    assert "does not exist" in str(error.value)


async def test_exists_uses_get(client, httpx_mock):
    httpx_mock.add_response(json=ORGANIZATION)
    assert await client.organizations.exists("006hf6230") is True
    httpx_mock.add_response(json=NOT_FOUND, status_code=404)
    assert await client.organizations.exists("00yjdzt39") is False
    assert [r.method for r in httpx_mock.get_requests()] == ["GET", "GET"]


async def test_search_sends_mapping_filters_and_options(client, httpx_mock):
    httpx_mock.add_response(json=PAGE)
    page = await client.organizations.search(
        {"types": ["education", "nonprofit"], "country.country_code": "NL"},
        query="university",
        advanced="established:[1900 TO 2000]",
        all_status=True,
        page=3,
    )
    assert page.total == PAGE["number_of_results"]
    assert page.page == 3
    assert last_request(httpx_mock).url.path == "/v2/organizations"
    assert last_params(httpx_mock) == {
        "filter": "types:education,types:nonprofit,country.country_code:NL",
        "page": "3",
        "query": "university",
        "query.advanced": "established:[1900 TO 2000]",
        "all_status": "true",
    }


async def test_search_sends_filter_model_with_aliases(client, httpx_mock):
    httpx_mock.add_response(json=PAGE)
    await client.organizations.search(
        OrganizationFilters(status="inactive", country_country_code="NL")
    )
    assert last_params(httpx_mock) == {
        "filter": "status:inactive,country.country_code:NL",
        "page": "1",
    }


async def test_search_omits_empty_filters_and_unsupported_options(client, httpx_mock):
    httpx_mock.add_response(json=PAGE)
    await client.organizations.search(None, page_size=50)
    assert last_params(httpx_mock) == {"page": "1"}


@pytest.mark.parametrize(
    ("kwargs", "fragment"),
    [
        ({"sort": "name"}, "does not support sorting"),
        ({"select": ["id"]}, "does not support field selection"),
        ({"cursor": "*"}, "does not support cursor paging"),
    ],
)
async def test_unsupported_options_raise_without_request(
    client, httpx_mock, kwargs, fragment
):
    with pytest.raises(ConfigurationError, match=fragment):
        await client.organizations.search(query="twente", **kwargs)
    assert not httpx_mock.get_requests()


async def test_page_500_is_sent_and_page_501_raises(client, httpx_mock):
    httpx_mock.add_response(json=PAGE)
    await client.organizations.search(query="university", page=500)
    assert last_params(httpx_mock)["page"] == "500"
    with pytest.raises(ConfigurationError, match="max_offset"):
        await client.organizations.search(query="university", page=501)
    assert len(httpx_mock.get_requests()) == 1


async def test_batch_get_is_disabled(client):
    with pytest.raises(ConfigurationError, match="disabled"):
        await client.organizations.batch_get(["006hf6230"])


@pytest.mark.parametrize(
    "operation", ["search", "count", "iterate", "match_affiliation", "get"]
)
async def test_errors_body_raises_configuration_error(client, httpx_mock, operation):
    """ROR reports rejected requests as HTTP 200 with an ``errors`` body."""
    httpx_mock.add_response(json=ERRORS_FILTER)
    with pytest.raises(ConfigurationError, match="filter key 'country' is illegal"):
        if operation == "search":
            await client.organizations.search({"country": "nl"})
        elif operation == "count":
            await client.organizations.count({"country": "nl"})
        elif operation == "iterate":
            [record async for record in client.organizations.iterate({"country": "nl"})]
        elif operation == "match_affiliation":
            await client.organizations.match_affiliation("University of Twente")
        else:
            await client.organizations.get("006hf6230")


async def test_page_errors_body_reads_ror_message(client, httpx_mock):
    httpx_mock.add_response(json=ERRORS_PAGE)
    with pytest.raises(ConfigurationError, match="outside of range 1-500"):
        await client.organizations.search(query="university", params={"page": 9000})


async def test_filter_value_with_comma_is_rejected(client):
    with pytest.raises(ConfigurationError, match="no ',' or ':'"):
        await client.organizations.search({"types": "education,nonprofit"})


async def test_count_reads_number_of_results(client, httpx_mock):
    httpx_mock.add_response(json=PAGE)
    assert await client.organizations.count(query="university of twente") == 132
    assert last_params(httpx_mock) == {"page": "1", "query": "university of twente"}


async def test_iterate_pages_until_total_without_duplicates(client, httpx_mock):
    first = [organization(f"{index:08x}") for index in range(20)]
    second = [organization(f"{index:08x}") for index in range(20, 40)]
    third = [organization(f"{index:08x}") for index in range(40, 45)]
    httpx_mock.add_response(json=envelope(first, number_of_results=45))
    httpx_mock.add_response(json=envelope(second, number_of_results=45))
    httpx_mock.add_response(json=envelope(third, number_of_results=45))

    records = [record async for record in client.organizations.iterate(query="x")]

    assert [r.url.params["page"] for r in httpx_mock.get_requests()] == [
        "1",
        "2",
        "3",
    ]
    assert len(records) == 45
    assert len({record.id for record in records}) == 45


async def test_iterate_limit_stops_after_one_page(client, httpx_mock):
    httpx_mock.add_response(
        json=envelope([organization(f"{index:08x}") for index in range(20)])
    )
    records = [
        record
        async for record in client.organizations.iterate(
            query="x", all_status=True, limit=5
        )
    ]
    assert len(records) == 5
    assert last_params(httpx_mock) == {
        "page": "1",
        "query": "x",
        "all_status": "true",
    }


async def test_iterate_forwards_query_options(client, httpx_mock):
    httpx_mock.add_response(json=envelope([]))
    records = [
        record
        async for record in client.organizations.iterate(
            {"status": ["inactive", "withdrawn"]},
            advanced="names.value:twente",
            all_status=True,
            limit=3,
        )
    ]
    assert records == []
    assert last_params(httpx_mock) == {
        "filter": "status:inactive,status:withdrawn",
        "page": "1",
        "query.advanced": "names.value:twente",
        "all_status": "true",
    }


async def test_match_affiliation_request_and_candidates(client, httpx_mock):
    payload = load_fixture("affiliation.json")
    httpx_mock.add_response(json=payload)
    matches = await client.organizations.match_affiliation(
        "  University of Twente, Enschede, Netherlands "
    )
    assert last_params(httpx_mock) == {
        "affiliation": "University of Twente, Enschede, Netherlands"
    }
    assert len(matches) == 3
    chosen = [match for match in matches if match.chosen]
    assert len(chosen) == 1
    assert chosen[0].score == 1.0
    assert chosen[0].organization.display_name == "University of Twente"
    assert matches[0].substring == "University of Twente, Enschede, Netherlands"


async def test_match_affiliation_rejects_blank_text(client, httpx_mock):
    with pytest.raises(ConfigurationError, match="non-empty"):
        await client.organizations.match_affiliation("   ")
    assert not httpx_mock.get_requests()


async def test_find_by_external_id_searches_every_spelling(client, httpx_mock):
    payload = load_fixture("search_page.json")
    payload["items"] = [
        organization(
            "006hf6230",
            external_ids=[
                {"type": "isni", "all": ["0000 0004 0399 8953"], "preferred": None}
            ],
        ),
        organization("027kueh35"),
    ]
    payload["number_of_results"] = 2
    httpx_mock.add_response(json=payload)
    httpx_mock.add_response(json=envelope([]))

    matches = await client.organizations.find_by_external_id(
        "0000000403998953", id_type="isni"
    )

    assert last_params(httpx_mock) == {
        "page": "1",
        "query.advanced": (
            'external_ids.all:"0000000403998953" '
            'OR external_ids.all:"0000 0004 0399 8953"'
        ),
        "all_status": "true",
    }
    assert [match.id for match in matches] == ["https://ror.org/006hf6230"]
    assert await client.organizations.find_by_external_id("9999 9999 9999 9999") == []


async def test_find_by_external_id_respects_id_type(client, httpx_mock):
    payload = envelope(
        [
            organization(
                "006hf6230", external_ids=[{"type": "wikidata", "all": ["Q1547084"]}]
            )
        ]
    )
    httpx_mock.add_response(json=payload)
    httpx_mock.add_response(json=payload)
    assert await client.organizations.find_by_external_id("q1547084") != []
    assert last_params(httpx_mock)["query.advanced"] == (
        'external_ids.all:"q1547084" OR external_ids.all:"Q1547084"'
    )
    assert (
        await client.organizations.find_by_external_id("Q1547084", id_type="isni") == []
    )


@pytest.mark.parametrize(
    "value", ["", "  ", 'a"b', "a\\b", "https://ror.org/006hf6230"]
)
async def test_find_by_external_id_rejects_unsearchable_values(
    client, httpx_mock, value
):
    with pytest.raises(ConfigurationError):
        await client.organizations.find_by_external_id(value)
    assert not httpx_mock.get_requests()


async def test_find_by_funder_doi_uses_fundref_id(client, httpx_mock):
    httpx_mock.add_response(json=envelope([load_fixture("organization_funder.json")]))
    matches = await client.organizations.find_by_funder_doi(
        "https://doi.org/10.13039/100000001"
    )
    assert last_params(httpx_mock)["query.advanced"] == ('external_ids.all:"100000001"')
    assert [match.id for match in matches] == ["https://ror.org/021nxhr62"]
    with pytest.raises(ValueError, match="Not a Crossref Funder Registry DOI"):
        await client.organizations.find_by_funder_doi("10.1234/abc")


async def test_base_url_override_points_elsewhere(httpx_mock, settings):
    httpx_mock.add_response(json=ORGANIZATION)
    client = RoriferClient(settings=settings, base_url="https://ror.example/v2/")
    async with client:
        await client.organizations.get("006hf6230")
    assert last_request(httpx_mock).url.path == "/v2/organizations/006hf6230"
