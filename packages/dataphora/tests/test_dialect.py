"""Dialect, filters, and helpers: pure tests without I/O (both variants)."""

from dataphora import (
    DATACITE_API_BASE_URL,
    DATACITE_DIALECT,
    DataphoraDoi,
    DataphoraEvent,
    DoiFilters,
    Publisher,
    serialize_filter_params,
)

from .conftest import doi_resource, plain_resource


def test_dialect_names_the_bracketed_parameters():
    assert DATACITE_API_BASE_URL == "https://api.datacite.org"
    assert DATACITE_DIALECT.page_size_param == "page[size]"
    assert DATACITE_DIALECT.page_param == "page[number]"
    assert DATACITE_DIALECT.cursor_param == "page[cursor]"
    assert DATACITE_DIALECT.cursor_start == "1"
    assert DATACITE_DIALECT.query_param == "query"
    assert DATACITE_DIALECT.sort_param == "sort"
    assert DATACITE_DIALECT.select_param == "fields[dois]"
    assert DATACITE_DIALECT.max_page_size == 1000
    assert DATACITE_DIALECT.default_page_size == 25
    assert DATACITE_DIALECT.iterate_page_size == 1000


def test_filter_model_dumps_with_aliases_and_joins_sequences():
    filters = DoiFilters(
        client_id="cern.zenodo",
        prefix=["10.5438", "10.5281"],
        has_affiliation=True,
        resource_type_id="dataset",
    )
    params = serialize_filter_params(filters)
    assert params == {
        "client-id": "cern.zenodo",
        "prefix": "10.5438,10.5281",
        "has-affiliation": "true",
        "resource-type-id": "dataset",
    }


def test_filter_params_drop_none_and_empty_values():
    assert serialize_filter_params(DoiFilters(prefix="10.5438", state=None)) == {
        "prefix": "10.5438"
    }
    assert serialize_filter_params(DoiFilters(prefix=[])) == {}


def test_filter_params_accept_plain_mappings():
    params = serialize_filter_params({"prefix": "10.5438", "bogus": 7})
    assert params == {"prefix": "10.5438", "bogus": "7"}
    assert serialize_filter_params(None) == {}


def test_filter_model_allows_extra_fields():
    filters = DoiFilters.model_validate({"not-yet-documented": "x"})
    extra = filters.model_dump(by_alias=True, exclude_none=True)
    assert extra == {"not-yet-documented": "x"}


def test_flatten_merges_attributes_into_the_model():
    record = doi_resource("10.5438/0012", viewCount=7, titles=[{"title": "T"}])
    doi = DataphoraDoi.model_validate(record)
    assert doi.id == "10.5438/0012"
    assert doi.doi == "10.5438/0012"
    assert doi.viewCount == 7
    assert doi.title == "T"
    assert doi.state == "findable"


def test_flatten_keeps_relationships_and_links():
    record = doi_resource(
        "10.5438/0012",
        relationships={
            "client": {"data": {"id": "datacite.datacite", "type": "clients"}}
        },
        links={"self": "https://api.datacite.org/dois/10.5438/0012"},
    )
    doi = DataphoraDoi.model_validate(record)
    assert doi.relationships is not None
    assert doi.client_id == "datacite.datacite"
    assert doi.provider_id is None
    assert doi.links is not None
    assert doi.links["self"].endswith("/dois/10.5438/0012")


def test_flatten_accepts_already_flat_records():
    doi = DataphoraDoi.model_validate({"id": "10.5438/0012", "doi": "10.5438/0012"})
    assert doi.doi == "10.5438/0012"


def test_integer_ids_are_stringified():
    parsed = DataphoraEvent.model_validate(
        plain_resource(12345, "events", **{"relation-type-id": "references"})
    )
    assert parsed.id == "12345"
    assert parsed.relation_type_id == "references"


def test_publisher_accepts_string_and_object():
    as_string = DataphoraDoi.model_validate(
        doi_resource("10.5438/0012", publisher="DataCite e.V.")
    )
    assert as_string.publisher == "DataCite e.V."
    as_object = DataphoraDoi.model_validate(
        doi_resource("10.5438/0012", publisher={"name": "DataCite e.V."})
    )
    assert isinstance(as_object.publisher, Publisher)
    assert as_object.publisher.name == "DataCite e.V."
