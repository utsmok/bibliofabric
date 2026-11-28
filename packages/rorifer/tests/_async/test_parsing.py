"""Parsing: real payloads, model coercions, page metadata."""

import pytest
from rorifer import (
    AffiliationMatch,
    APIError,
    Organization,
    OrganizationFilters,
    RorDump,
    RoriferClient,
)

from ..conftest import load_fixture

ORGANIZATION = load_fixture("organization.json")
FUNDER = load_fixture("organization_funder.json")
PAGE = load_fixture("search_page.json")


async def test_organization_fields_from_real_payload(client, httpx_mock):
    httpx_mock.add_response(json=ORGANIZATION)
    record = await client.organizations.get("006hf6230")
    assert record.display_name == "University of Twente"
    assert record.status == "active"
    assert record.established == 1961
    assert record.types == ["education", "funder"]
    assert record.domains == ["utwente.nl"]
    assert record.external_ids_of_type("fundref") == [
        "501100001834",
        "501100007661",
        "501100009404",
        "501100015450",
    ]
    assert record.external_ids_of_type("wikidata") == ["Q1547084"]
    assert record.names[0].lang == "nl"
    location = record.locations[0]
    assert location.geonames_id == 2756071
    assert location.geonames_details is not None
    assert location.geonames_details.country_code == "NL"
    assert location.geonames_details.lat == 52.21833
    assert {rel.type for rel in record.relationships} == {"child", "related"}
    assert record.admin is not None
    assert record.admin.last_modified is not None
    assert record.admin.last_modified.date == "2026-07-20"
    assert record.links[0].value == "https://www.utwente.nl"


async def test_inactive_record_keeps_relationships(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("organization_inactive.json"))
    record = await client.organizations.get("001z21q04")
    assert record.status == "inactive"
    assert [(rel.type, rel.id) for rel in record.relationships] == [
        ("child", "https://ror.org/03saykv37"),
        ("child", "https://ror.org/00kneq391"),
        ("successor", "https://ror.org/05f82e368"),
    ]


def test_display_name_prefers_ror_display_then_label():
    def name(*types, value="x"):
        return {"lang": None, "types": list(types), "value": value}

    display = Organization.model_validate(
        {"names": [name("alias", value="UT"), name("ror_display", value="Twente")]}
    )
    label = Organization.model_validate(
        {
            "names": [
                name("acronym", value="UT"),
                name("label", value="Universiteit Twente"),
            ]
        }
    )
    alias = Organization.model_validate({"names": [name("alias", value="UT")]})
    assert display.display_name == "Twente"
    assert label.display_name == "Universiteit Twente"
    assert alias.display_name == "UT"
    assert Organization.model_validate({}).display_name is None


def test_nulls_and_scalars_coerce_and_extras_are_kept():
    record = Organization.model_validate(
        {
            "id": None,
            "names": None,
            "types": "education",
            "domains": [None, "utwente.nl", None],
            "external_ids": None,
            "names_count": 2,
        }
    )
    assert record.id is None
    assert record.names == []
    assert record.types == ["education"]
    assert record.domains == ["utwente.nl"]
    assert record.external_ids == []
    assert record.model_extra == {"names_count": 2}


def test_funder_record_from_real_payload():
    record = Organization.model_validate(FUNDER)
    assert "funder" in record.types
    assert record.external_ids_of_type("fundref") == [
        "100000001",
        "100015388",
        "100023581",
    ]
    assert len(record.relationships) == 35


async def test_search_page_meta_carries_facets(client, httpx_mock):
    httpx_mock.add_response(json=PAGE)
    page = await client.organizations.search(query="university")
    assert page.total == 132
    assert page.next_cursor is None
    assert page.meta["types"] == PAGE["meta"]["types"]
    assert page.meta["types"][0] == {
        "id": "education",
        "title": "education",
        "count": 132,
    }
    assert page.meta["statuses"] == [{"id": "active", "title": "active", "count": 132}]
    assert page.meta["countries"] == PAGE["meta"]["countries"]
    assert page.meta["continents"] == PAGE["meta"]["continents"]
    assert "meta" not in page.meta
    assert page.meta["time_taken"] == PAGE["time_taken"]
    assert [record.display_name for record in page.results] == [
        "Nyenrode Business University",
        PAGE["items"][1]["names"][1]["value"],
    ]


def test_filter_model_accepts_both_spellings():
    filters = OrganizationFilters(country_country_code="NL")
    assert filters.model_dump(by_alias=True, exclude_none=True) == {
        "country.country_code": "NL"
    }
    by_alias = OrganizationFilters.model_validate({"country.country_code": "NL"})
    assert by_alias.country_country_code == "NL"
    extra = OrganizationFilters.model_validate({"bogus": 1})
    assert extra.model_dump(by_alias=True, exclude_none=True) == {"bogus": 1}


def test_dump_models_from_real_payload():
    hits = load_fixture("zenodo_search.json")["hits"]["hits"]
    dump = RorDump.model_validate(hits[0])
    assert dump.record_id == 24378467
    assert dump.concept_id == 6347574
    assert dump.publication_date == "2026-11-19"
    assert dump.version == "v2.16"
    assert dump.title == "ROR Data"
    assert dump.zip_file is not None
    assert dump.zip_file.key == "v2.16-2026-11-19-ror-data.zip"
    assert dump.zip_file.size == 40861154
    assert dump.zip_url == (
        "https://zenodo.org/api/records/24378467/files/"
        "v2.16-2026-11-19-ror-data.zip/content"
    )
    assert dump.links is not None
    assert dump.links.self_html == "https://zenodo.org/records/24378467"
    assert (
        dump.links.latest == "https://zenodo.org/api/records/24378467/versions/latest"
    )


def test_dump_without_zip_has_no_url():
    dump = RorDump.model_validate({"id": 1, "files": [{"key": "a.csv"}]})
    assert dump.zip_file is None
    assert dump.zip_url is None


def test_affiliation_match_from_real_payload():
    items = load_fixture("affiliation.json")["items"]
    matches = [AffiliationMatch.model_validate(item) for item in items]
    assert [match.chosen for match in matches] == [True, False, False]
    assert [match.score for match in matches] == [1.0, 0.86, 0.83]
    assert {match.matching_type for match in matches} == {"SINGLE SEARCH"}
    second = matches[1].organization
    assert second is not None
    assert second.id == "https://ror.org/00ssh1q19"
    assert matches[0].substring == "University of Twente, Enschede, Netherlands"


def test_client_exposes_resources(settings):
    client = RoriferClient(settings=settings)
    assert client.base_url == "https://api.ror.org/v2"
    assert client.default_headers == {"Accept": "application/json"}
    assert client.organizations.path == "organizations"
    assert client.organizations is client.organizations
    assert client.dumps is client.dumps


@pytest.mark.parametrize("operation", ["search", "count", "match_affiliation", "get"])
async def test_body_that_is_not_an_object_raises_api_error(
    client, httpx_mock, operation
):
    """A body of another shape is an error, not an empty answer."""
    httpx_mock.add_response(json=["not", "an", "envelope"])
    with pytest.raises(APIError, match="not a JSON object"):
        if operation == "search":
            await client.organizations.search(query="university")
        elif operation == "count":
            await client.organizations.count(query="university")
        elif operation == "match_affiliation":
            await client.organizations.match_affiliation("University of Twente")
        else:
            await client.organizations.get("006hf6230")


@pytest.mark.parametrize(
    ("body", "operation"),
    [
        ({"number_of_results": 1}, "search"),
        ({"number_of_results": 1}, "iterate"),
        ({"items": "none"}, "match_affiliation"),
    ],
)
async def test_envelope_without_items_list_raises_api_error(
    client, httpx_mock, body, operation
):
    """Every list route carries ``items``, even when it has no match."""
    httpx_mock.add_response(json=body)
    with pytest.raises(APIError, match="no items list"):
        if operation == "search":
            await client.organizations.search(query="university")
        elif operation == "iterate":
            [
                record
                async for record in client.organizations.iterate(query="university")
            ]
        else:
            await client.organizations.match_affiliation("University of Twente")


def test_total_without_number_of_results_is_none(client):
    """``number_of_results`` absent from an object reads as an unknown total."""
    assert client.unwrapper.total({"items": []}) is None
