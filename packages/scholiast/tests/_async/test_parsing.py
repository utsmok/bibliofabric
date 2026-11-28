"""Model parsing against trimmed real-API payloads."""

import pytest
from scholiast import (
    Author,
    Citation,
    ExternalIds,
    Paper,
    PaperMatch,
    Patent,
    PatentCitations,
    Reference,
    ScholiastUnwrapper,
    SnippetPaper,
    SnippetSearchResult,
)

from ..conftest import load_fixture

PAPER = load_fixture("paper.json")
CITATIONS = load_fixture("citations.json")
REFERENCES = load_fixture("references.json")
AUTHOR = load_fixture("author.json")
AUTOCOMPLETE = load_fixture("autocomplete.json")
PATENT = load_fixture("patent.json")
SNIPPETS = load_fixture("snippets.json")


def test_paper_parses_every_documented_field():
    paper = Paper.model_validate(PAPER)
    assert paper.paperId == "a5de30adc5c22bc86e8cfabe7fbd07c052d196a8"
    assert paper.title == "Nanometer scale thermometry in a living cell"
    assert paper.year == 2013
    assert paper.citationCount == 1847
    assert paper.referenceCount == 41
    assert paper.influentialCitationCount == 29
    assert paper.venue == "Nature"
    assert paper.journal is not None
    assert paper.openAccessPdf is not None
    assert paper.openAccessPdf.status == "GREEN"
    assert paper.externalIds is not None
    assert paper.externalIds.DOI == "10.1038/nature12373"
    assert paper.externalIds.CorpusId == 4314121
    assert paper.tldr is not None
    assert paper.tldr.text
    assert paper.authors
    assert paper.authors[0].name
    assert paper.s2FieldsOfStudy
    assert paper.s2FieldsOfStudy[0].source


def test_external_ids_keys_are_exact():
    ids = ExternalIds.model_validate(PAPER["externalIds"])
    assert ids.ArXiv == "1304.1068"
    assert ids.PubMed == "23903748"
    assert ids.PubMedCentral == "4221854"
    assert ids.MAG == "2159974629"
    assert ids.DBLP is None


def test_paper_tolerates_missing_and_extra_fields():
    paper = Paper.model_validate({"paperId": "abc", "brandNewField": 7})
    assert paper.title is None
    assert paper.model_extra is not None
    assert paper.model_extra["brandNewField"] == 7


def test_citation_and_reference_parse():
    citation = Citation.model_validate(CITATIONS["data"][0])
    assert citation.citingPaper is not None
    assert citation.citingPaper.paperId
    assert citation.contexts == []
    assert citation.intents == []
    assert citation.isInfluential is False
    reference = Reference.model_validate(REFERENCES["data"][0])
    assert reference.citedPaper is not None
    assert reference.citedPaper.paperId


def test_author_parses_counts():
    author = Author.model_validate(AUTHOR)
    assert author.authorId == "1741101"
    assert author.name == "Oren Etzioni"
    assert author.hIndex == 89
    assert author.paperCount == 262
    assert author.citationCount == 46292


def test_autocomplete_candidates_parse():
    records = AUTOCOMPLETE["matches"]
    paper = Paper.model_validate({"paperId": records[0]["id"]})
    assert paper.paperId == records[0]["id"]
    assert records[0]["authorsYear"]


def test_patent_parses_minimal_record():
    patent = Patent.model_validate(PATENT)
    assert patent.title
    assert patent.ucid


def test_snippet_result_parses():
    result = SnippetSearchResult.model_validate(SNIPPETS)
    assert result.retrievalVersion == 1
    match = result.data[0]
    assert match.score == 0.87
    assert match.snippet is not None
    assert match.snippet.snippetKind == "bodyText"
    assert match.snippet.snippetOffset == [0, 61]
    assert match.snippet.annotations is not None
    assert match.snippet.annotations.sentences[0].end == 61
    ref_mention = match.snippet.annotations.refMentions[0]
    assert ref_mention.matchedPaperCorpusId == 215416146
    assert match.paper is not None
    assert match.paper.corpusId == 215416146


def test_patent_parses_the_detail_record():
    """``claims`` is one text; the party names are lists of strings."""
    patent = Patent.model_validate(load_fixture("patent_detail.json"))
    assert patent.ucid == "US10296086B2"
    assert patent.claims and patent.claims.startswith("1. A system for processing")
    assert patent.claimCount == 23
    assert patent.inventors == ["Noam Rimon", "Xiaodong (Crusoe) Mao", "Xiaoyong Ye"]
    assert patent.assignees == ["Sony Interactive Entertainment Inc."]
    assert patent.cpcCodes[0] == "G06F3/014"
    assert patent.source == "patent_ontology"
    assert patent.office is None


def test_patent_citations_envelope_parses():
    """``data`` holds the citing patents; the last page has no ``next``."""
    body = load_fixture("patent_citations.json")
    envelope = PatentCitations.model_validate({**body, "data": [*body["data"], None]})
    assert envelope.total == 1
    assert envelope.offset == 0
    assert envelope.next is None
    assert envelope.data[0].ucid == "US11532318B2"
    assert envelope.data[0].publicationYear == 2022


def test_author_parses_aliases_and_normalized_affiliations():
    """``normalizedAffiliations`` holds ``{rorId, rorDisplayName}`` objects."""
    affiliation = {"rorId": "https://ror.org/01qr0p675", "rorDisplayName": "A lab"}
    author_record = Author.model_validate(
        {
            "authorId": "1741101",
            "aliases": ["O. Etzioni"],
            "normalizedAffiliations": [affiliation],
        }
    )
    assert author_record.aliases == ["O. Etzioni"]
    parsed = author_record.normalizedAffiliations[0]
    assert parsed.rorId == affiliation["rorId"]
    assert parsed.rorDisplayName == "A lab"


def test_unwrapper_total_accepts_a_numeric_string():
    assert ScholiastUnwrapper().total({"total": "102687"}) == 102687
    assert ScholiastUnwrapper().total({"total": None}) is None


@pytest.mark.parametrize("authors", [[{"authorId": "1", "name": "A"}], ["A"]])
def test_snippet_paper_authors_accept_objects_and_strings(authors):
    paper = SnippetPaper.model_validate({"corpusId": 1, "authors": authors})
    assert paper.authors == authors


def test_snippet_retrieval_version_accepts_a_string():
    result = SnippetSearchResult.model_validate({"data": [], "retrievalVersion": "1"})
    assert result.retrievalVersion == "1"


def test_paper_match_from_record_splits_match_score():
    record = load_fixture("paper_match.json")["data"][0]
    match = PaperMatch.from_record(record)
    assert match.matchScore == 260.92
    assert match.paper is not None
    assert match.paper.paperId == record["paperId"]
    assert match.paper.matchScore is None


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ({"data": [{"paperId": "a"}], "next": 1, "offset": 0}, 1),
        ({"matches": [{"id": "a"}]}, 1),
        ({"recommendedPapers": [{"paperId": "a"}]}, 1),
        ({"paperId": "a"}, 0),
        ([{"paperId": "a"}], 0),
    ],
)
def test_unwrapper_results_shapes(body, expected):
    unwrapper = ScholiastUnwrapper()
    assert len(unwrapper.results(body)) == expected


def test_unwrapper_next_cursor_reads_next_and_token():
    unwrapper = ScholiastUnwrapper()
    assert unwrapper.next_cursor({"next": 10}) == "10"
    assert unwrapper.next_cursor({"token": "abc"}) == "abc"
    assert unwrapper.next_cursor({}) is None
    assert unwrapper.total({"total": 5}) == 5
    assert unwrapper.total({}) is None
    assert unwrapper.meta({"data": [], "offset": 0, "next": 5}) == {
        "offset": 0,
        "next": 5,
    }
