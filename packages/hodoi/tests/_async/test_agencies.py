"""The ``/ra/`` registration agency lookup: request shape and parsing."""

import pytest
from hodoi import ConfigurationError, ValidationError

from ..conftest import load_fixture

PAIR = load_fixture("ra_pair.json")
UNKNOWN = load_fixture("ra_unknown.json")
INVALID = load_fixture("ra_invalid.json")


def last_request(httpx_mock):
    return httpx_mock.get_requests()[-1]


async def test_agency_of_one_doi(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("ra_crossref.json"))
    answer = await client.agency("10.1038/nature12373")
    assert answer.DOI == "10.1038/nature12373"
    assert answer.RA == "Crossref"
    assert answer.status is None
    assert last_request(httpx_mock).url.path == "/ra/10.1038/nature12373"


async def test_agency_of_a_medra_doi(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("ra_medra.json"))
    assert (await client.agency("10.1400/56174")).RA == "mEDRA"


async def test_agency_accepts_doi_urls(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("ra_datacite.json"))
    answer = await client.agency("https://doi.org/10.5281/zenodo.1238808")
    assert answer.RA == "DataCite"
    assert last_request(httpx_mock).url.path == "/ra/10.5281/zenodo.1238808"


async def test_agencies_of_many_dois_join_with_commas(client, httpx_mock):
    httpx_mock.add_response(json=PAIR)
    answers = await client.agencies(["10.1038/nature12373", "10.5281/zenodo.1238808"])
    assert [answer.RA for answer in answers] == ["Crossref", "DataCite"]
    path = last_request(httpx_mock).url.path
    assert path == "/ra/10.1038/nature12373,10.5281/zenodo.1238808"


async def test_agencies_percent_encode_special_characters(client, httpx_mock):
    """A comma inside a DOI is encoded, so it does not split the list."""
    httpx_mock.add_response(json=load_fixture("ra_unknown.json"))
    await client.agencies(["10.1000/a#b?c", "https://doi.org/10.1000/x%2Cy"])
    raw_path = last_request(httpx_mock).url.raw_path
    assert raw_path == b"/ra/10.1000/a%23b%3Fc,10.1000/x%2Cy"


async def test_agencies_cut_the_query_and_fragment_of_doi_urls(client, httpx_mock):
    """A raw ``?`` or ``#`` in a URL starts the query string or the fragment."""
    httpx_mock.add_response(json=load_fixture("ra_unknown.json"))
    await client.agencies("https://doi.org/10.1038/nature12373?from=mail#top")
    assert last_request(httpx_mock).url.path == "/ra/10.1038/nature12373"


async def test_agencies_encode_non_ascii_dois_as_utf8(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("ra_unknown.json"))
    await client.agencies("10.1000/テスト")
    assert (
        last_request(httpx_mock).url.raw_path
        == b"/ra/10.1000/%E3%83%86%E3%82%B9%E3%83%88"
    )


async def test_agency_of_unknown_doi_is_a_status_answer(client, httpx_mock):
    httpx_mock.add_response(json=UNKNOWN)
    answer = await client.agency("10.9999/nope")
    assert answer.RA is None
    assert answer.status == "DOI does not exist"


async def test_agency_of_invalid_doi_is_a_status_answer(client, httpx_mock):
    httpx_mock.add_response(json=INVALID)
    answer = await client.agency("not-a-doi")
    assert answer.status == "Invalid DOI"


async def test_agencies_chunks_long_lists(client, httpx_mock):
    dois = [f"10.1038/nature{i}x" for i in range(101)]
    httpx_mock.add_response(json=[{"DOI": dois[0], "status": "DOI does not exist"}])
    httpx_mock.add_response(json=[{"DOI": dois[100], "status": "DOI does not exist"}])
    answers = await client.agencies(dois)
    assert len(answers) == 2
    paths = [request.url.path for request in httpx_mock.get_requests()]
    assert len(paths) == 2
    assert paths[0].count("10.1038/") == 100
    assert paths[1].count("10.1038/") == 1


async def test_agencies_split_long_dois_by_path_length(client, httpx_mock):
    """Ten DOIs of 900 characters do not fit one path under the budget."""
    dois = ["10.1000/" + "a" * 892 for _ in range(10)]
    for size in (4, 4, 2):
        entry = {"DOI": dois[0], "status": "DOI does not exist"}
        httpx_mock.add_response(json=[entry] * size)
    answers = await client.agencies(dois)
    assert len(answers) == 10
    paths = [request.url.path for request in httpx_mock.get_requests()]
    assert [path.count("10.1000/") for path in paths] == [4, 4, 2]
    assert all(len(path) <= 4000 for path in paths)


async def test_agencies_sends_invalid_strings_for_the_status_answer(client, httpx_mock):
    """``/ra/`` answers malformed strings itself; nothing is rejected client-side."""
    httpx_mock.add_response(json=INVALID)
    answer = (await client.agencies(["https://doi.org/not-a-doi"]))[0]
    assert answer.DOI == "not-a-doi"
    assert answer.status == "Invalid DOI"
    assert httpx_mock.get_requests()[0].url.path == "/ra/not-a-doi"


@pytest.mark.parametrize("value", [[], ["10.1038/nature12373", " "]])
async def test_agencies_rejects_empty_input(client, httpx_mock, value):
    with pytest.raises(ConfigurationError, match="at least one DOI|blank DOI"):
        await client.agencies(value)
    assert not httpx_mock.get_requests()


async def test_agencies_raises_on_non_list_body(client, httpx_mock):
    httpx_mock.add_response(json={"unexpected": True})
    with pytest.raises(ConfigurationError, match="non-list"):
        await client.agency("10.1038/nature12373")


async def test_agency_raises_on_an_empty_answer(client, httpx_mock):
    httpx_mock.add_response(json=[])
    with pytest.raises(ConfigurationError, match="no entry"):
        await client.agency("10.1038/nature12373")


async def test_agencies_raises_on_an_entry_that_is_not_an_object(client, httpx_mock):
    """No row is dropped silently: an answer of another shape is an error."""
    httpx_mock.add_response(json=["not-an-entry"])
    with pytest.raises(ValidationError, match="AgencyAnswer"):
        await client.agencies("10.1038/nature12373")
