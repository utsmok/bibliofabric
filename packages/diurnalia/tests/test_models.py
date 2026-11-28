"""Models against real trimmed payloads, without I/O."""

from diurnalia import Article, Journal

from .conftest import load_fixture

JOURNAL_PAGE = load_fixture("journal_by_issn.json")
JOURNAL_BY_ID = load_fixture("journal_get_by_id.json")
ARTICLE_PAGE = load_fixture("article_by_doi.json")


def test_journal_fields_from_real_payload():
    record = Journal.model_validate(JOURNAL_PAGE["results"][0])
    assert record.id == "2fdf1470373343b7bd4f825179c685f5"
    assert record.title == "PLoS ONE"
    assert record.issns == ["1932-6203"]
    assert record.publisher_name == "Public Library of Science (PLoS)"
    bibjson = record.bibjson
    assert bibjson.alternative_title == "PLOS ONE"
    assert bibjson.oa_start == 2006
    assert bibjson.publication_time_weeks == 29
    assert bibjson.boai is True
    assert bibjson.language == ["EN"]
    assert [subject.term for subject in bibjson.subject] == ["Medicine", "Science"]
    license_entry = bibjson.license[0]
    assert license_entry.type == "CC BY"
    assert license_entry.by is True
    assert license_entry.nc is False
    assert bibjson.apc is not None
    assert bibjson.apc.has_apc is True
    assert bibjson.apc.max[0].price == 2477
    assert bibjson.apc.max[0].currency == "USD"
    assert bibjson.editorial is not None
    assert bibjson.editorial.review_process == ["Single anonymous peer review"]
    assert bibjson.preservation is not None
    assert bibjson.preservation.service == ["CLOCKSS", "PMC"]
    assert bibjson.pid_scheme is not None
    assert bibjson.pid_scheme.scheme == ["DOI"]
    assert bibjson.ref is not None
    assert bibjson.ref.journal == "https://journals.plos.org/plosone/"
    assert record.admin is not None
    assert record.admin.ticked is True
    assert record.created_date == "2007-03-30T10:53:19Z"


def test_journal_get_by_id_shape():
    record = Journal.model_validate(JOURNAL_BY_ID)
    assert record.title
    assert record.bibjson.publisher is not None
    assert record.last_manual_update is not None


def test_article_fields_from_real_payload():
    record = Article.model_validate(ARTICLE_PAGE["results"][0])
    assert record.title == (
        "Hunger in Vulnerable Families in Southeastern Europe: "
        "Associations With Mental Health and Violence"
    )
    assert record.doi == "10.3389/fpubh.2020.00115"
    assert record.issns == ["2296-2565"]
    bibjson = record.bibjson
    assert bibjson.journal is not None
    assert bibjson.journal.publisher == "Frontiers Media S.A."
    assert bibjson.journal.volume == "8"
    assert bibjson.journal.country == "CH"
    assert bibjson.year == "2020"
    assert bibjson.month == "4"
    assert bibjson.abstract and bibjson.abstract.startswith("Background:")
    assert len(bibjson.author) == 7
    assert bibjson.author[0].name == "Elena Jansen"
    assert bibjson.author[0].affiliation is not None
    assert {link.content_type for link in bibjson.link} == {"HTML"}
    assert bibjson.subject[0].scheme == "LCC"


def test_article_without_doi_reports_none():
    record = Article.model_validate({"id": "x", "bibjson": {"title": "No DOI"}})
    assert record.doi is None
    assert record.issns == []
