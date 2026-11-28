"""Outgoing request shape: paths, params, headers, batching, guards."""

import json
from functools import partial

import pytest
from scholiast import (
    AuthError,
    ConfigurationError,
    NotFoundError,
    PaperSearchFilters,
    ScholiastClient,
    ScholiastSettings,
)

from ..conftest import (
    author,
    list_envelope,
    load_fixture,
    paper,
    search_envelope,
)

PAPER = load_fixture("paper.json")
PAGE = load_fixture("search.json")
CITATIONS = load_fixture("citations.json")
PAPER_BATCH = load_fixture("paper_batch.json")
AUTHOR = load_fixture("author.json")
AUTHOR_SEARCH = load_fixture("author_search.json")
AUTHOR_BATCH = load_fixture("author_batch.json")
REC = load_fixture("rec_forpaper.json")
RELEASES = load_fixture("release_list.json")
RELEASE = load_fixture("release_latest.json")
BULK = load_fixture("bulk_search.json")


def last_request(httpx_mock):
    return httpx_mock.get_requests()[-1]


def last_params(httpx_mock) -> dict[str, str]:
    return dict(last_request(httpx_mock).url.params)


def fix_null(records, **fields):
    """Fixture lists with trailing nulls confuse model parsing; strip them."""
    return [record for record in records if record is not None]


async def test_get_paper_by_doi_id_form(client, httpx_mock):
    httpx_mock.add_response(json=PAPER)
    record = await client.papers.get("DOI:10.1038/nature12373")
    assert record.paperId == PAPER["paperId"]
    request = last_request(httpx_mock)
    assert request.url.path == "/graph/v1/paper/DOI:10.1038/nature12373"


async def test_get_sends_fields_param(client, httpx_mock):
    httpx_mock.add_response(json=PAPER)
    await client.papers.get("DOI:10.1038/nature12373", select=["title", "year"])
    assert last_params(httpx_mock) == {"fields": "title,year"}


async def test_get_raises_not_found(client, httpx_mock):
    httpx_mock.add_response(
        json={"error": "Paper with id DOI:10.x not found"}, status_code=404
    )
    with pytest.raises(NotFoundError):
        await client.papers.get("DOI:10.1038/does-not-exist")


async def test_api_key_header_present_when_set(httpx_mock):
    settings = ScholiastSettings(
        _env_file=None,
        api_key="test-key-value",
        max_requests_per_second=1_000_000.0,
        max_retries=0,
        timeout=5.0,
    )
    httpx_mock.add_response(json=PAPER)
    client = ScholiastClient(settings=settings)
    async with client:
        await client.papers.get("DOI:10.1038/nature12373")
    request = httpx_mock.get_requests()[0]
    assert request.headers["x-api-key"] == "test-key-value"


async def test_no_api_key_header_without_key(client, httpx_mock):
    httpx_mock.add_response(json=PAPER)
    await client.papers.get("DOI:10.1038/nature12373")
    assert "x-api-key" not in last_request(httpx_mock).headers


async def test_search_maps_query_filters_offset_limit(client, httpx_mock):
    httpx_mock.add_response(json=PAGE)
    page = await client.papers.search(
        PaperSearchFilters(year="2020-2023", minCitationCount=50),
        query="photosynthesis",
        fields=["title", "year", "citationCount"],
        page=2,
        page_size=5,
    )
    assert page.total == PAGE["total"]
    assert page.next_cursor == str(PAGE["next"])
    assert last_request(httpx_mock).url.path == "/graph/v1/paper/search"
    assert last_params(httpx_mock) == {
        "limit": "5",
        "offset": "5",
        "query": "photosynthesis",
        "fields": "title,year,citationCount",
        "year": "2020-2023",
        "minCitationCount": "50",
    }


async def test_search_rejects_offset_past_cap(client):
    with pytest.raises(ConfigurationError, match="max_offset"):
        await client.papers.search(query="x", page=2000)


async def test_bulk_search_first_and_continuation(client, httpx_mock):
    httpx_mock.add_response(json=BULK)
    page = await client.papers.bulk_search(
        "crispr", fields=["title", "year"], params={"sort": "publicationDate:asc"}
    )
    assert page.total == BULK["total"]
    assert page.next_cursor == BULK["token"]
    assert "limit" not in last_request(httpx_mock).url.params
    assert last_params(httpx_mock)["sort"] == "publicationDate:asc"

    httpx_mock.add_response(json=load_fixture("bulk_next.json"))
    second = await client.papers.bulk_search("crispr", token=page.next_cursor)
    assert second.results
    assert last_params(httpx_mock)["token"] == BULK["token"]


async def test_bulk_iterate_follows_token(client, httpx_mock):
    httpx_mock.add_response(json=BULK)
    httpx_mock.add_response(json=load_fixture("bulk_next.json"))
    records = [record async for record in client.papers.bulk_iterate("crispr", limit=3)]
    assert len(records) == 3
    assert [r.url.params.get("token") for r in httpx_mock.get_requests()] == [
        None,
        BULK["token"],
    ]


async def test_batch_posts_ids_and_drops_nulls(client, httpx_mock):
    httpx_mock.add_response(json=PAPER_BATCH)
    papers = await client.papers.batch(
        ["ARXIV:2106.15928", "DOI:10.9999/nope", "DOI:10.9999/also-nope"],
        fields=["title", "year"],
    )
    request = last_request(httpx_mock)
    assert request.method == "POST"
    assert request.url.path == "/graph/v1/paper/batch"
    assert request.url.params["fields"] == "title,year"
    assert json.loads(request.read()) == {
        "ids": ["ARXIV:2106.15928", "DOI:10.9999/nope", "DOI:10.9999/also-nope"]
    }
    assert len(papers) == 1
    assert papers[0].paperId == fix_null(PAPER_BATCH)[0]["paperId"]


async def test_batch_empty_ids_sends_nothing(client, httpx_mock):
    assert await client.papers.batch([]) == []
    assert not httpx_mock.get_requests()


async def test_citations_and_references(client, httpx_mock):
    httpx_mock.add_response(json=CITATIONS)
    citations = await client.papers.citations(
        "DOI:10.1038/nature12373",
        fields=["title", "contexts", "isInfluential"],
        limit=2,
        offset=5,
    )
    assert last_request(httpx_mock).url.raw_path.split(b"?")[0] == (
        b"/graph/v1/paper/DOI%3A10.1038%2Fnature12373/citations"
    )
    assert last_params(httpx_mock) == {
        "fields": "title,contexts,isInfluential",
        "limit": "2",
        "offset": "5",
    }
    assert citations.results[0].citingPaper is not None
    assert citations.next_cursor == str(CITATIONS["next"])

    httpx_mock.add_response(json=load_fixture("references.json"))
    references = await client.papers.references("DOI:10.1038/nature12373")
    assert last_request(httpx_mock).url.path.endswith("/references")
    assert references.results[0].citedPaper is not None


async def test_paper_authors_page(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("paper_authors.json"))
    authors = await client.papers.authors("DOI:10.1038/nature12373", limit=3)
    assert authors.results[0].name
    assert authors.next_cursor == "5"


async def test_autocomplete_reads_matches(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("autocomplete.json"))
    candidates = await client.papers.autocomplete("semanti")
    assert last_request(httpx_mock).url.path == "/graph/v1/paper/autocomplete"
    assert candidates
    assert candidates[0].title


async def test_autocomplete_rejects_blank(client):
    with pytest.raises(ConfigurationError, match="non-empty"):
        await client.papers.autocomplete("  ")


async def test_search_match_returns_first_candidate(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("paper_match.json"))
    match = await client.papers.search_match("nanometer scale thermometry")
    assert last_request(httpx_mock).url.path == "/graph/v1/paper/search/match"
    assert match.paper is not None
    assert match.paper.paperId == "a5de30adc5c22bc86e8cfabe7fbd07c052d196a8"
    assert match.matchScore == 260.92


async def test_search_match_raises_when_no_candidate(client, httpx_mock):
    httpx_mock.add_response(json={"data": []})
    with pytest.raises(NotFoundError):
        await client.papers.search_match("zzz no such title zzz")


async def test_author_get_search_papers_and_batch(client, httpx_mock):
    httpx_mock.add_response(json=AUTHOR)
    record = await client.authors.get("1741101")
    assert record.name == "Oren Etzioni"

    httpx_mock.add_response(json=AUTHOR_SEARCH)
    page = await client.authors.search(query="adam smith", page_size=5)
    assert page.total == AUTHOR_SEARCH["total"]
    assert last_request(httpx_mock).url.path == "/graph/v1/author/search"

    httpx_mock.add_response(json=list_envelope([author("1")]))
    papers = await client.authors.papers("1741101", fields=["title"])
    assert last_request(httpx_mock).url.path == "/graph/v1/author/1741101/papers"
    assert papers.results[0].authorId == "1"

    httpx_mock.add_response(json=AUTHOR_BATCH)
    authors = await client.authors.batch(["1741101", "99999999"])
    assert len(authors) == 1
    assert authors[0].authorId == "1741101"
    request = last_request(httpx_mock)
    assert request.url.path == "/graph/v1/author/batch"
    assert "fields" not in request.url.params


async def test_recommendations_for_paper_and_for_list(client, httpx_mock):
    httpx_mock.add_response(json=REC)
    papers = await client.recommendations.for_paper(
        "DOI:10.1038/nature12373", fields=["title"], limit=5
    )
    request = last_request(httpx_mock)
    assert request.url.host == "api.semanticscholar.org"
    assert request.url.path == (
        "/recommendations/v1/papers/forpaper/DOI:10.1038/nature12373"
    )
    assert papers

    httpx_mock.add_response(json=load_fixture("rec_forlist.json"))
    listed = await client.recommendations.for_list(
        ["ARXIV:2106.15928"], ["DOI:10.1038/nature12373"], fields=["title"]
    )
    request = last_request(httpx_mock)
    assert request.method == "POST"
    assert request.url.path == "/recommendations/v1/papers/"
    assert json.loads(request.read()) == {
        "positivePaperIds": ["ARXIV:2106.15928"],
        "negativePaperIds": ["DOI:10.1038/nature12373"],
    }
    assert listed


async def test_recommendations_for_list_rejects_empty_lists(client):
    with pytest.raises(ConfigurationError, match="positive or negative"):
        await client.recommendations.for_list([])


async def test_datasets_releases_release_and_latest(client, httpx_mock):
    httpx_mock.add_response(json=RELEASES)
    releases = await client.datasets.releases()
    assert releases[0] == "2022-05-10"

    httpx_mock.add_response(json=RELEASE)
    release = await client.datasets.latest()
    assert release.release_id == "2026-11-24"
    assert release.datasets
    assert release.datasets[0].name == "abstracts"


async def test_datasets_dataset_and_diffs(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("dataset_metadata.json"))
    dataset = await client.datasets.dataset("abstracts")
    assert last_request(httpx_mock).url.path == (
        "/datasets/v1/release/latest/dataset/abstracts"
    )
    assert dataset.files

    httpx_mock.add_response(json=load_fixture("dataset_diffs.json"))
    diffs = await client.datasets.diffs("abstracts", "2026-11-17", "2026-11-24")
    assert last_request(httpx_mock).url.path == (
        "/datasets/v1/diffs/2026-11-17/to/2026-11-24/abstracts"
    )
    assert diffs.diffs[0].update_files


async def test_snippets_and_patents(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("snippets.json"))
    result = await client.snippets.search("protein folding", limit=1)
    assert result.data[0].score is not None

    httpx_mock.add_response(json=load_fixture("patent.json"))
    patent_record = await client.patents.get("US10296086B2")
    assert last_request(httpx_mock).url.path == "/graph/v1/patent/US10296086B2"
    assert patent_record.title

    httpx_mock.add_response(json=list_envelope([{"ucid": "US1"}], total=1))
    patents = await client.patents.search("neural network", limit=5)
    assert last_request(httpx_mock).url.path == "/graph/v1/patent/search"
    assert patents.results[0].ucid == "US1"

    httpx_mock.add_response(json=load_fixture("patent_citations.json"))
    citations = await client.patents.outbound_citations(
        "CorpusId:4314121", fields=["title"], limit=5, offset=0
    )
    request = last_request(httpx_mock)
    assert request.url.raw_path.split(b"?")[0] == (
        b"/graph/v1/patent/outbound-citations/CorpusId%3A4314121"
    )
    assert dict(request.url.params) == {
        "fields": "title",
        "limit": "5",
        "offset": "0",
    }
    assert citations.total == 1
    assert citations.next is None
    assert citations.data[0].ucid == "US11532318B2"


async def test_base_url_override_points_elsewhere(httpx_mock, settings):
    httpx_mock.add_response(json=PAPER)
    client = ScholiastClient(settings=settings, base_url="https://s2.example/graph/v1/")
    async with client:
        await client.papers.get("DOI:10.1038/nature12373")
    assert (
        last_request(httpx_mock).url.path == "/graph/v1/paper/DOI:10.1038/nature12373"
    )


async def test_sub_list_routes_encode_the_id(client, httpx_mock):
    """Every route encodes the id as one path segment, as ``get()`` does."""
    httpx_mock.add_response(json=list_envelope([{"citingPaper": PAPER}]))
    await client.papers.citations("URL:https://example.org/a b?x=1")
    assert last_request(httpx_mock).url.raw_path == (
        b"/graph/v1/paper/URL%3Ahttps%3A%2F%2Fexample.org%2Fa%20b%3Fx%3D1/citations"
    )


async def test_blank_ids_are_rejected_before_a_request(client, httpx_mock):
    calls = [
        lambda: client.papers.citations(" "),
        lambda: client.papers.references(""),
        lambda: client.papers.authors("  "),
        lambda: client.authors.papers(" "),
        lambda: client.patents.get(""),
        lambda: client.patents.outbound_citations("  "),
        lambda: client.datasets.release(" "),
        lambda: client.datasets.dataset("papers", release_id=""),
        lambda: client.recommendations.for_paper(" "),
    ]
    for call in calls:
        with pytest.raises(ConfigurationError, match="non-empty"):
            await call()
    assert not httpx_mock.get_requests()


async def test_inactive_api_key_raises_auth_error(httpx_mock):
    """A rejected key is an error and never a silent fall back to no key."""
    settings = ScholiastSettings(
        _env_file=None,
        api_key="inactive-key",
        max_requests_per_second=1_000_000.0,
        max_retries=0,
        timeout=5.0,
    )
    httpx_mock.add_response(json={"message": "Forbidden"}, status_code=403)
    async with ScholiastClient(settings=settings) as keyed:
        get = partial(keyed.papers.get, "DOI:10.1038/nature12373")
        with pytest.raises(AuthError, match="403"):
            await get()
    requests = httpx_mock.get_requests()
    assert len(requests) == 1
    assert requests[0].headers["x-api-key"] == "inactive-key"


async def test_references_keep_the_source_paper_in_meta(client, httpx_mock):
    """The references envelope carries the source paper beside the list."""
    httpx_mock.add_response(
        json={
            "offset": 0,
            "next": 2,
            "citingPaperInfo": {"title": "Nanometer scale thermometry"},
            "data": [{"citedPaper": PAPER}],
        }
    )
    page = await client.papers.references("DOI:10.1038/nature12373")
    assert page.next_cursor == "2"
    assert page.meta["citingPaperInfo"]["title"] == "Nanometer scale thermometry"
    assert page.results[0].citedPaper is not None


async def test_bulk_search_last_page_has_no_token(client, httpx_mock):
    """The last page carries ``token`` as ``null``, not as a string."""
    httpx_mock.add_response(json={"total": 1, "token": None, "data": [PAPER]})
    page = await client.papers.bulk_search("crispr")
    assert page.total == 1
    assert page.next_cursor is None


async def test_patent_without_citing_patents_raises_not_found(client, httpx_mock):
    """The route answers 404 when no patent cites the paper."""
    httpx_mock.add_response(json={"error": "Not found"}, status_code=404)
    with pytest.raises(NotFoundError):
        await client.patents.outbound_citations("DOI:10.1038/nature12373")


async def test_batch_get_is_disabled(client, httpx_mock):
    """The API batches through POST only, so ``batch_get`` refuses early."""
    for resource in (client.papers, client.authors):
        with pytest.raises(ConfigurationError, match="batch_get is disabled"):
            await resource.batch_get(["DOI:10.1038/nature12373"])
    assert not httpx_mock.get_requests()


async def test_citations_pass_extra_params(client, httpx_mock):
    httpx_mock.add_response(json=CITATIONS)
    await client.papers.citations(
        "DOI:10.1038/nature12373",
        fields=["title"],
        params={"publicationDateOrYear": "2020:2021"},
    )
    assert last_params(httpx_mock)["publicationDateOrYear"] == "2020:2021"


async def test_search_match_passes_filters(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("paper_match.json"))
    match = await client.papers.search_match(
        "nanometer scale thermometry", filters=PaperSearchFilters(year="2013")
    )
    assert match.paper is not None
    assert last_request(httpx_mock).url.path == "/graph/v1/paper/search/match"
    assert last_params(httpx_mock)["year"] == "2013"


async def test_author_papers_pass_extra_params(client, httpx_mock):
    httpx_mock.add_response(
        json=list_envelope([paper("a5de30adc5c22bc86e8cfabe7fbd07c052d196a8")])
    )
    await client.authors.papers(
        "1741101",
        fields=["title"],
        params={"publicationDateOrYear": "2013"},
    )
    assert last_params(httpx_mock)["publicationDateOrYear"] == "2013"


async def test_recommendations_for_paper_passes_params(client, httpx_mock):
    httpx_mock.add_response(json=REC)
    await client.recommendations.for_paper(
        "DOI:10.1038/nature12373", params={"from": "all-cs"}, limit=3
    )
    assert last_params(httpx_mock) == {"from": "all-cs", "limit": "3"}


async def test_snippet_search_passes_params(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("snippets.json"))
    await client.snippets.search(
        "protein folding", limit=2, params={"year": "2020-2021"}
    )
    assert last_request(httpx_mock).url.path == "/graph/v1/snippet/search"
    assert last_params(httpx_mock) == {
        "query": "protein folding",
        "limit": "2",
        "year": "2020-2021",
    }


async def test_search_routes_reject_blank_queries(client, httpx_mock):
    with pytest.raises(ConfigurationError, match="non-empty"):
        await client.snippets.search("  ")
    with pytest.raises(ConfigurationError, match="non-empty"):
        await client.patents.search(" ")
    assert not httpx_mock.get_requests()


async def test_author_search_page_size_is_capped_at_1000(client, httpx_mock):
    """Author search takes 1000 records a page where paper search takes 100."""
    httpx_mock.add_response(json=AUTHOR_SEARCH)
    await client.authors.search(query="adam smith", page=2, page_size=1000)
    assert last_params(httpx_mock)["limit"] == "1000"
    assert last_params(httpx_mock)["offset"] == "1000"

    httpx_mock.add_response(json=PAGE)
    await client.papers.search(query="x", page_size=1000)
    assert last_params(httpx_mock)["limit"] == "100"


async def test_author_search_rejects_offset_past_cap(client):
    with pytest.raises(ConfigurationError, match="max_offset"):
        await client.authors.search(query="x", page=10_000)


async def test_patent_search_sends_query_limit_and_offset(client, httpx_mock):
    httpx_mock.add_response(json=search_envelope([{"ucid": "US1"}]))
    page = await client.patents.search(
        "neural network", fields=["title"], limit=5, offset=10
    )
    assert last_params(httpx_mock) == {
        "query": "neural network",
        "fields": "title",
        "limit": "5",
        "offset": "10",
    }
    assert page.total == 1
    assert page.next_cursor == "1"
