"""Tests for stavrophora Pydantic models."""

from stavrophora.models import ApiResponse, Work


def test_work_parses_kebab_aliases(sample_work_json):
    work = Work.model_validate(sample_work_json)
    assert work.doi == "10.1038/nature12373"
    assert work.container_title == ["Nature"]
    assert work.is_referenced_by_count == 500
    assert work.references_count == 50
    assert work.issn == ["0028-0836", "1476-4687"]
    assert work.primary_title == "Nanometre-scale thermometry in a living cell"


def test_work_issued_date_parts(sample_work_json):
    work = Work.model_validate(sample_work_json)
    assert work.issued is not None
    assert work.issued.date_parts == [[2013, 7, 31]]
    assert work.issued.year == 2013


def test_work_nested_models(sample_work_json):
    work = Work.model_validate(sample_work_json)
    assert work.author[0].family == "Kucsko"
    assert work.author[1].name == "Scientific Collective"
    assert work.author[0].orcid == "https://orcid.org/0000-0002-1234-5678"
    assert work.license[0].content_version == "vor"
    assert work.funder[0].doi == "10.13039/501100001711"


def test_contributor_parses_uppercase_orcid():
    work = Work.model_validate(
        {"author": [{"ORCID": "http://orcid.org/0000-0003-4154-1711"}]}
    )
    assert work.author[0].orcid == "http://orcid.org/0000-0003-4154-1711"


def test_work_accepts_string_or_list_update_to():
    update = [{"DOI": "10.1234/retraction", "type": "retraction"}]
    work = Work.model_validate({"update-to": update})
    assert work.update_to == update
    assert Work.model_validate({"update-to": "10.1234/retraction"}).update_to == (
        "10.1234/retraction"
    )


def test_work_extra_fields_allowed():
    """Undocumented API fields land in extra without failing validation."""
    work = Work.model_validate(
        {
            "DOI": "10.1234/x",
            "brand-new-field": {"nested": True},
            "another-one": 7,
        }
    )
    assert work.doi == "10.1234/x"
    extra = work.model_extra or {}
    assert extra["brand-new-field"] == {"nested": True}
    assert extra["another-one"] == 7


def test_work_safe_coercion():
    work = Work.model_validate(
        {
            "DOI": None,
            "title": [None, "Real Title"],
            "subject": None,
            "publisher": None,
            "edition-number": None,
        }
    )
    assert work.doi is None  # Optional fields stay None
    assert work.title == ["Real Title"]  # null elements stripped
    assert work.subject == []
    assert work.publisher is None  # Optional[SafeStr] preserves None


def test_work_null_numeric_defaults():
    work = Work.model_validate({"DOI": "10.1/x", "is-referenced-by-count": None})
    assert work.is_referenced_by_count == 0


def test_member_field_accepts_string_or_int():
    assert Work.model_validate({"member": "298"}).member == "298"
    assert Work.model_validate({"member": 298}).member == 298


def test_api_response_envelope(sample_works_response):
    response = ApiResponse[Work].model_validate(sample_works_response)
    assert response.status == "ok"
    assert response.message_type == "work-list"
    assert response.message.total_results == 1
    assert response.message.items[0].doi == "10.1038/nature12373"


def test_api_response_missing_next_cursor(sample_works_response):
    response = ApiResponse[Work].model_validate(sample_works_response)
    assert response.message.next_cursor is None


def test_journal_title_accepts_scalar_or_list():
    """Single-item /journals/{issn} returns title as a bare string (live-verified)."""
    from stavrophora.models import Journal

    single = Journal.model_validate({"title": "Nature", "ISSN": ["0028-0836"]})
    assert single.title == ["Nature"]
    assert single.primary_title == "Nature"

    listed = Journal.model_validate({"title": ["Nature"], "ISSN": ["0028-0836"]})
    assert listed.title == ["Nature"]


def test_member_prefix_entries_are_objects():
    """Live /members/{id} returns prefix entries as {name, value} objects."""
    from stavrophora.models import Member

    member = Member.model_validate(
        {"id": 78, "prefix": [{"name": "Elsevier", "value": "10.1016"}]}
    )
    assert member.prefix[0]["value"] == "10.1016"
