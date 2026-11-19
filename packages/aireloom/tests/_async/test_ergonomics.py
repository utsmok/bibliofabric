"""Ergonomics helpers: relation vocabulary, by_orcid, find_variants, get_fields."""

from aireloom import RELATION_INVERSES, relation_inverse

from .conftest import json_response, load, params_of

EMPTY_PAGE = {"header": {"numFound": 0}, "results": []}


def test_relation_inverse_pairs():
    assert relation_inverse("Cites") == "IsCitedBy"
    assert relation_inverse("IsCitedBy") == "Cites"
    assert relation_inverse("IsRelatedTo") == "IsRelatedTo"
    assert relation_inverse("NotARelation") is None


def test_relation_vocabulary_matches_relations_info():
    for entry in load("relations_info.json"):
        assert RELATION_INVERSES[entry["relation"]] == entry["inverse"]
        assert RELATION_INVERSES[entry["inverse"]] == entry["relation"]


async def test_by_orcid_normalizes_and_returns_list(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("rp_orcid_page.json")))
    httpx_mock.add_response(**json_response(load("rp_orcid_page.json")))
    results = await client.research_products.by_orcid(
        "https://orcid.org/0000-0002-1825-0097"
    )
    assert await client.research_products.by_orcid("0000-0002-1825-0097", limit=5)
    filters = [params_of(r)["filter"] for r in httpx_mock.get_requests()]
    assert filters == [
        "authorships.author.orcid:0000-0002-1825-0097",
        "authorships.author.orcid:0000-0002-1825-0097",
    ]
    sizes = [params_of(r)["page_size"] for r in httpx_mock.get_requests()]
    assert sizes == ["100", "5"]
    assert [r.id for r in results] == ["dedup_wf_002::288a07aa5a6b71815aadfc57207c5167"]


async def test_find_variants_dedupes_and_keeps_pending(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("org_variants_p1.json")))
    httpx_mock.add_response(**json_response(load("org_variants_p2.json")))
    orgs = await client.organizations.find_variants(["university of twente", "utwente"])
    ids = [org.id for org in orgs]
    assert len(ids) == len(set(ids))
    assert ids.count("openorgs____::5051dc5a570e109474ca2f2d846ebe37") == 1
    assert "pending_org_::447de8613c24e020737a0654146651e8" in ids
    assert "pending_org_::360cda1f7aeed6f2fad3ffccc2503904" in ids
    queries = [params_of(r)["search"] for r in httpx_mock.get_requests()]
    assert queries == ["university of twente", "utwente"]


async def test_find_variants_country_filter(httpx_mock, client):
    httpx_mock.add_response(**json_response(EMPTY_PAGE))
    await client.organizations.find_variants(["twente"], country="NL")
    assert params_of(httpx_mock.get_request())["filter"] == "country:NL"


async def test_get_fields_selects_and_ors_ids(httpx_mock, client):
    httpx_mock.add_response(**json_response(load("rp_select_page.json")))
    ids = [
        "06cdd3ff4700::3c8734759ca685b966b1d737c37daeed",
        "06cdd3ff4700::5369fb2bf6e438896254176095d5b022",
    ]
    records = await client.research_products.get_fields(
        ids, ["id", "mainTitle", "publicationDate"]
    )
    params = params_of(httpx_mock.get_request())
    assert params["select"] == "id,mainTitle,publicationDate"
    assert params["filter"] == "id:" + "|".join(ids)
    assert params["page_size"] == "2"
    assert [record.id for record in records] == ids
    assert records[0].mainTitle


async def test_get_fields_empty_ids_sends_no_request(httpx_mock, client):
    assert await client.research_products.get_fields([], ["id"]) == []
    assert httpx_mock.get_requests() == []


async def test_get_fields_splits_ids_into_batch_size_requests(httpx_mock, client):
    httpx_mock.add_response(**json_response(EMPTY_PAGE), is_reusable=True)
    ids = [f"x::{i}" for i in range(client.research_products.batch_size + 1)]
    await client.research_products.get_fields(ids, ["id"])
    requests = httpx_mock.get_requests()
    assert len(requests) == 2
    assert params_of(requests[1])["filter"] == f"id:{ids[-1]}"
