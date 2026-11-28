"""Parsing: real payloads, model coercions, the value wrapper accessor."""

import pytest
from orchis import (
    ActivitiesSummary,
    ConfigurationError,
    Funding,
    FuzzyDate,
    OrchisClient,
    OrchisRecord,
    OrchisSettings,
    Person,
    TextValue,
    Work,
    text,
)

from .conftest import load_fixture

ORCID_ID = "0000-0002-1694-233X"


def test_record_from_real_payload():
    record = OrchisRecord.model_validate(load_fixture("record.json"))
    identifier = record.orcid_identifier
    assert identifier is not None and identifier.path == ORCID_ID
    history = record.history
    assert history is not None
    assert history.claimed is True
    assert history.last_modified_date is not None
    assert history.last_modified_date.value == 1758797020758
    person = record.person
    assert person is not None and person.name is not None
    assert person.name.given_names is not None
    assert person.name.given_names.text == "Thomas B."
    summary = record.activities_summary
    assert summary is not None
    works = summary.works
    assert works is not None and works.put_codes()[0] == 145464015
    employments = summary.employments
    assert employments is not None and employments.put_codes() == [85908]
    fundings = summary.fundings
    assert fundings is not None and fundings.put_codes() == [63665]
    assert summary.distinctions is not None
    assert summary.distinctions.affiliation_group == []
    assert summary.qualifications is not None
    assert summary.qualifications.affiliation_group == []


def test_person_from_real_payload():
    person = Person.model_validate(load_fixture("person.json"))
    name = person.name
    assert name is not None
    assert name.family_name is not None
    assert name.family_name.text == "Hickey"
    assert name.path == ORCID_ID
    assert person.biography is None
    urls = person.researcher_urls
    assert urls is not None
    assert [url.url_name for url in urls.researcher_url][:2] == [
        "ISNI ID 0000 0000 2368 8144",
        "Blog",
    ]
    identifiers = person.external_identifiers
    assert identifiers is not None
    identifier = identifiers.external_identifier[0]
    assert identifier.type == "Scopus Author ID"
    assert identifier.put_code == 447495
    other_names = person.other_names
    assert other_names is not None
    assert other_names.other_name[0].content == "Thom Hickey"


def test_activities_from_real_payload():
    summary = ActivitiesSummary.model_validate(load_fixture("activities.json"))
    educations = summary.educations
    assert educations is not None
    group = educations.affiliation_group[0].summaries[0]
    assert group["education-summary"]["put-code"] == 85904
    works = summary.works
    assert works is not None
    first = works.group[0].work_summary[0]
    assert first.title is not None
    assert first.title.title is not None
    assert first.title.title.text == "Parsing and Matching Dates in VIAF"
    services = summary.services
    assert services is not None and services.put_codes() == [10777936]
    peer_reviews = summary.peer_reviews
    assert peer_reviews is not None and peer_reviews.group == []


def test_work_and_funding_from_real_payload():
    work = Work.model_validate(load_fixture("work.json"))
    assert work.put_code == 145464015
    assert work.title is not None
    assert work.title.subtitle is not None
    assert work.title.subtitle.text == "Issue 26, 2014-10-21"
    assert work.journal_title is not None
    assert work.journal_title.text == "Code4Lib Journal"
    assert work.publication_date is not None
    assert work.publication_date.iso() == "2014-10-21"
    citation = work.citation
    assert citation is not None and citation.citation_type == "formatted-unspecified"
    contributors = work.contributors
    assert contributors is not None
    second = contributors.contributor[1].orcid
    assert second is not None and second.path == ORCID_ID
    funding = Funding.model_validate(load_fixture("funding.json"))
    assert funding.put_code == 63665
    organization = funding.organization
    assert organization is not None
    disambiguated = organization.disambiguated_organization
    assert disambiguated is not None
    assert disambiguated.identifier == "http://dx.doi.org/10.13039/100000179"
    assert funding.start_date is not None
    assert funding.start_date.iso() == "1979-08"


def test_value_accessor_reads_wrapped_text():
    assert text(TextValue(value="2020")) == "2020"
    assert text(None) is None
    assert FuzzyDate(year=TextValue(value="1977")).iso() == "1977"
    assert (
        FuzzyDate(year=TextValue(value="2014"), month=TextValue(value="10")).iso()
        == "2014-10"
    )


def test_nulls_coerce_and_extras_are_kept():
    work = Work.model_validate(
        {"title": {"title": None}, "journal-title": None, "bogus-extra": 3}
    )
    assert work.title is not None
    assert work.title.title is None
    assert work.journal_title is None
    assert work.model_extra == {"bogus-extra": 3}


def test_client_exposes_resources():
    client = OrchisClient(
        settings=OrchisSettings(
            _env_file=None, access_token=None, client_id=None, client_secret=None
        )
    )
    assert client.base_url == "https://pub.orcid.org/v3.0"
    assert client.default_headers == {"Accept": "application/json"}
    assert client.record.suffix == "record"
    assert client.person is client.person
    assert client.activities is client.activities
    assert client.expanded_search is client.expanded_search
    assert client.search is client.search


def test_one_half_of_the_client_credentials_raises():
    settings = OrchisSettings(
        _env_file=None, access_token=None, client_id="APP-1", client_secret=None
    )
    with pytest.raises(ConfigurationError, match="client_secret"):
        OrchisClient(settings=settings)
