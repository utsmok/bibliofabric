"""Outgoing request shape: paths, Accept headers, paging, guards."""

import pytest
from orchis import ConfigurationError, NotFoundError, OrchisClient

from ..conftest import (
    ORCID_ID,
    expanded_envelope,
    expanded_result,
    load_fixture,
    solr_envelope,
    solr_result,
)

RECORD = load_fixture("record.json")
WORK = load_fixture("work.json")


def last_request(httpx_mock):
    return httpx_mock.get_requests()[-1]


def last_params(httpx_mock) -> dict[str, str]:
    return dict(last_request(httpx_mock).url.params)


async def test_record_get_uses_orcid_path_and_accept_json(client, httpx_mock):
    httpx_mock.add_response(json=RECORD)
    record = await client.record.get(f"https://orcid.org/{ORCID_ID}")
    assert record.orcid_identifier.path == ORCID_ID
    request = last_request(httpx_mock)
    assert request.url.path == f"/v3.0/{ORCID_ID}/record"
    assert request.headers["accept"] == "application/json"


async def test_record_exists_uses_get(client, httpx_mock):
    httpx_mock.add_response(json=RECORD)
    assert await client.record.exists(ORCID_ID) is True
    httpx_mock.add_response(status_code=404)
    assert await client.record.exists("0000-0000-0000-0000") is False
    assert [r.method for r in httpx_mock.get_requests()] == ["GET", "GET"]


async def test_record_get_raises_not_found(client, httpx_mock):
    httpx_mock.add_response(status_code=404)
    with pytest.raises(NotFoundError):
        await client.record.get("0000-0000-0000-0000")


async def test_person_sections_hit_their_routes(client, httpx_mock):
    for suffix, method, fixture in [
        ("person", client.person.get, "person.json"),
        ("personal-details", client.person.personal_details, "personal_details.json"),
        ("researcher-urls", client.person.researcher_urls, "researcher_urls.json"),
        ("address", client.person.addresses, "address.json"),
        ("keywords", client.person.keywords, "keywords.json"),
        (
            "external-identifiers",
            client.person.external_identifiers,
            "external_identifiers.json",
        ),
    ]:
        httpx_mock.add_response(json=load_fixture(fixture))
        await method(ORCID_ID)
        assert last_request(httpx_mock).url.path == f"/v3.0/{ORCID_ID}/{suffix}"


async def test_missing_biography_returns_none(client, httpx_mock):
    httpx_mock.add_response(status_code=404)
    assert await client.person.biography(ORCID_ID) is None
    assert last_request(httpx_mock).url.path == f"/v3.0/{ORCID_ID}/biography"


async def test_missing_emails_returns_none(client, httpx_mock):
    httpx_mock.add_response(status_code=404)
    assert await client.person.emails(ORCID_ID) is None
    assert last_request(httpx_mock).url.path == f"/v3.0/{ORCID_ID}/emails"


async def test_person_not_found_propagates_when_not_empty_404(client, httpx_mock):
    httpx_mock.add_response(status_code=404)
    with pytest.raises(NotFoundError):
        await client.person.get("0000-0000-0000-0000")


async def test_activities_summary(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("activities.json"))
    summary = await client.activities.get(ORCID_ID)
    assert summary.works.put_codes()
    assert last_request(httpx_mock).url.path == f"/v3.0/{ORCID_ID}/activities"


async def test_activities_sections(client, httpx_mock):
    sections = {
        "works": (client.activities.works, "works.json"),
        "educations": (client.activities.educations, "educations.json"),
        "employments": (client.activities.employments, "employments.json"),
        "fundings": (client.activities.fundings, "fundings.json"),
        "peer-reviews": (client.activities.peer_reviews, "peer_reviews.json"),
    }
    for suffix, (method, fixture) in sections.items():
        httpx_mock.add_response(json=load_fixture(fixture))
        section = await method(ORCID_ID)
        assert section is not None
        assert last_request(httpx_mock).url.path == f"/v3.0/{ORCID_ID}/{suffix}"


async def test_empty_activities_section_returns_none(client, httpx_mock):
    httpx_mock.add_response(status_code=404)
    assert await client.activities.distinctions(ORCID_ID) is None
    assert last_request(httpx_mock).url.path == f"/v3.0/{ORCID_ID}/distinctions"


async def test_single_items_use_singular_routes(client, httpx_mock):
    httpx_mock.add_response(json=WORK)
    work = await client.activities.work(ORCID_ID, 145464015)
    assert work.put_code == 145464015
    assert last_request(httpx_mock).url.path == f"/v3.0/{ORCID_ID}/work/145464015"

    httpx_mock.add_response(json=load_fixture("education.json"))
    education = await client.activities.education(ORCID_ID, 85904)
    assert education["put-code"] == 85904
    assert last_request(httpx_mock).url.path == f"/v3.0/{ORCID_ID}/education/85904"

    httpx_mock.add_response(json=load_fixture("funding.json"))
    funding = await client.activities.funding(ORCID_ID, 63665)
    assert funding.put_code == 63665
    assert last_request(httpx_mock).url.path == f"/v3.0/{ORCID_ID}/funding/63665"

    httpx_mock.add_response(json=load_fixture("membership.json"))
    membership = await client.activities.affiliation_item(
        ORCID_ID, "membership", 14806385
    )
    assert membership["put-code"] == 14806385
    assert last_request(httpx_mock).url.path == (
        f"/v3.0/{ORCID_ID}/membership/14806385"
    )


async def test_affiliation_item_rejects_unknown_kind(client):
    with pytest.raises(ConfigurationError, match="kind must be one of"):
        await client.activities.affiliation_item(ORCID_ID, "bogus", 1)


async def test_work_representation_returns_text(client, httpx_mock):
    httpx_mock.add_response(
        content=b"<work:work/>",
        headers={"Content-Type": "application/xml;charset=UTF-8"},
    )
    body = await client.activities.representation(ORCID_ID, "work/145464015")
    assert body == "<work:work/>"
    request = last_request(httpx_mock)
    assert request.headers["accept"] == "application/xml"


async def test_record_representation_returns_text(client, httpx_mock):
    httpx_mock.add_response(content=b"<record/>")
    body = await client.record.representation(ORCID_ID)
    assert body == "<record/>"
    assert last_request(httpx_mock).headers["accept"] == "application/xml"


async def test_expanded_search_sends_q_rows_start(client, httpx_mock):
    httpx_mock.add_response(
        json=expanded_envelope([expanded_result("0000-0002-4189-3154")])
    )
    page = await client.expanded_search.search(
        query="family-name:Kucsko", page_size=2, page=1
    )
    assert page.total == 1
    assert page.page == 1
    assert last_request(httpx_mock).url.path == "/v3.0/expanded-search/"
    assert last_params(httpx_mock) == {
        "q": "family-name:Kucsko",
        "rows": "2",
        "start": "2",
    }


async def test_expanded_search_requires_query(client, httpx_mock):
    with pytest.raises(ConfigurationError, match="requires a query"):
        await client.expanded_search.search()
    assert not httpx_mock.get_requests()


async def test_solr_search_sends_q_and_reads_results(client, httpx_mock):
    httpx_mock.add_response(json=solr_envelope([solr_result("0000-0002-4189-3154")]))
    page = await client.search.search(query="family-name:Kucsko", page_size=2)
    assert page.total == 1
    assert page.results[0].orcid_identifier.path == "0000-0002-4189-3154"
    assert last_params(httpx_mock) == {
        "q": "family-name:Kucsko",
        "rows": "2",
        "start": "0",
    }


async def test_expanded_search_iterate_stops_at_total(client, httpx_mock):
    first = [expanded_result(f"0000-0002-4189-315{i}") for i in range(2)]
    httpx_mock.add_response(json=expanded_envelope(first, num_found=3))
    httpx_mock.add_response(json=expanded_envelope(first, num_found=3))
    records = [
        record
        async for record in client.expanded_search.iterate(
            query="family-name:Kucsko", page_size=2, limit=3
        )
    ]
    assert len(records) == 3
    assert [r.url.params["start"] for r in httpx_mock.get_requests()] == ["0", "2"]


async def test_base_url_override_points_elsewhere(httpx_mock, settings):
    httpx_mock.add_response(json=RECORD)
    client = OrchisClient(settings=settings, base_url="https://orcid.example/v3.0/")
    async with client:
        await client.record.get(ORCID_ID)
    assert last_request(httpx_mock).url.path == f"/v3.0/{ORCID_ID}/record"
