"""Live OpenCitations smoke tests against the real APIs.

The module sends eighteen requests at the default pace of 3 requests per
second, far below the documented limit of 180 requests per minute. No
credentials are needed.
"""

import pytest
from opcitato import OpcitatoClient, OpcitatoSettings

pytestmark = pytest.mark.live_api

#: The operations of both APIs answer 200 with these example identifiers
#: (drawn from the official documentation examples on 2026-11-27).
CITED = "doi:10.1108/jd-12-2013-0166"
CITING = "doi:10.7717/peerj-cs.421"
OCI = "06101801781-06180334099"
VENUE = "issn:0138-9130"
PERSON = "orcid:0000-0002-8420-0696"
EDITOR = "orcid:0000-0003-2098-4759"
#: A real DOI with parentheses, angle brackets, colons, and a semicolon.
SICI_DOI = "doi:10.1002/(SICI)1097-4636(199823)43:3<338::AID-JBM16>3.0.CO;2-B"

INDEX_SPARQL = (
    "SELECT ?ci ?citing ?cited WHERE { "
    "?ci <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> "
    "<http://purl.org/spar/cito/Citation> ; "
    "<http://purl.org/spar/cito/hasCitingEntity> ?citing ; "
    "<http://purl.org/spar/cito/hasCitedEntity> ?cited } LIMIT 3"
)
META_SPARQL = (
    "SELECT ?br ?title WHERE { "
    "?br <http://purl.org/dc/terms/title> ?title ; "
    "<http://prismstandard.org/namespaces/basic/2.0/publicationDate> ?date } LIMIT 3"
)


@pytest.fixture
async def live_client():
    async with OpcitatoClient(settings=OpcitatoSettings(_env_file=None)) as client:
        yield client


async def test_citations_smoke(live_client):
    rows = await live_client.index.citations(CITED)
    assert rows
    row = rows[0]
    assert row.cited_identifiers[1].value == "10.1108/jd-12-2013-0166"
    assert row.journal_sc in {"yes", "no"}


async def test_citations_csv_smoke(live_client):
    rows = await live_client.index.citations(CITED, format="csv")
    assert [row.oci for row in rows]
    assert rows[0].citing


async def test_references_smoke(live_client):
    rows = await live_client.index.references(CITING)
    assert rows
    assert rows[0].citing_identifiers[1].scheme == "doi"


async def test_citation_smoke(live_client):
    row = await live_client.index.citation(OCI)
    assert row is not None
    assert row.oci == OCI


async def test_counts_smoke(live_client):
    incoming = await live_client.index.citation_count(CITED)
    outgoing = await live_client.index.reference_count(CITING)
    venue = await live_client.index.venue_citation_count(VENUE)
    assert isinstance(incoming, int) and incoming > 0
    assert isinstance(outgoing, int) and outgoing > 0
    assert isinstance(venue, int) and venue > incoming


async def test_unknown_id_answers_empty_list_smoke(live_client):
    rows = await live_client.index.citations("doi:10.9999/nonexistent.000")
    assert rows == []


async def test_unknown_id_count_smoke(live_client):
    # The API answered a zero row on 2026-11-28 and an empty list on
    # 2026-11-27; the client reports both without raising.
    count = await live_client.index.citation_count("doi:10.9999/nonexistent.000")
    assert count in (0, None)


async def test_special_characters_in_the_id_smoke(live_client):
    count = await live_client.index.citation_count(SICI_DOI)
    assert isinstance(count, int) and count > 0


async def test_filter_and_sort_smoke(live_client):
    rows = await live_client.index.citations(CITED, filter="creation:>2019-12")
    assert rows
    assert all(row.creation >= "2020" for row in rows)
    ordered = await live_client.index.citations(CITED, sort="desc(creation)")
    assert ordered[0].creation >= ordered[-1].creation


async def test_meta_metadata_smoke(live_client):
    rows = await live_client.meta.metadata("doi:10.1007/978-1-4020-9632-7")
    assert rows[0].title == "Adaptive Environmental Management"
    assert rows[0].identifiers[0].scheme == "doi"


async def test_meta_metadata_multi_id_smoke(live_client):
    rows = await live_client.meta.metadata(
        ["doi:10.1108/jd-12-2013-0166", "doi:10.1016/j.websem.2012.08.001"]
    )
    assert len(rows) == 2
    ids = {row.identifiers[0].value for row in rows}
    assert ids == {"10.1108/jd-12-2013-0166", "10.1016/j.websem.2012.08.001"}


async def test_meta_author_smoke(live_client):
    rows = await live_client.meta.author(PERSON)
    assert rows
    assert any(PERSON in row.author for row in rows)


async def test_meta_editor_smoke(live_client):
    rows = await live_client.meta.editor(EDITOR)
    assert rows
    assert any(EDITOR in row.editor for row in rows)


async def test_index_sparql_smoke(live_client):
    result = await live_client.index.sparql(INDEX_SPARQL)
    rows = result.rows()
    assert 0 < len(rows) <= 3
    assert all(row["ci"].startswith("https://w3id.org/oc/index/ci/") for row in rows)
    assert result.meta["result-size-total"] == len(rows)


async def test_meta_sparql_post_smoke(live_client):
    result = await live_client.meta.sparql(META_SPARQL, method="POST")
    rows = result.rows()
    assert 0 < len(rows) <= 3
    assert all(row["br"].startswith("https://w3id.org/oc/meta/br/") for row in rows)
    assert all(row["title"] for row in rows)
