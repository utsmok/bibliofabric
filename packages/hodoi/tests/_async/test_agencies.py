"""The ``/ra/`` registration agency lookup: request shape and parsing."""

import pytest
from hodoi import ConfigurationError, normalize_doi

from ..conftest import load_fixture

PAIR = load_fixture("ra_pair.json")
UNKNOWN = load_fixture("ra_unknown.json")
INVALID = load_fixture("ra_invalid.json")


def last_request(httpx_mock):
    return httpx_mock.get_requests()[-1]


def test_normalize_doi_forms():
    assert normalize_doi("10.1038/nature12373") == "10.1038/nature12373"
    assert normalize_doi("https://doi.org/10.1038/nature12373") == "10.1038/nature12373"
    assert (
        normalize_doi("http://dx.doi.org/10.1038/NATURE12373") == "10.1038/NATURE12373"
    )
    assert normalize_doi("doi:10.1038/nature12373") == "10.1038/nature12373"
    assert normalize_doi("  10.1038/nature12373 ") == "10.1038/nature12373"


@pytest.mark.parametrize(
    "value", ["", "10.1038", "1038/nature", "https://example.com/10.1/abc"]
)
def test_normalize_doi_rejects_non_dois(value):
    with pytest.raises(ConfigurationError):
        normalize_doi(value)


async def test_agency_of_one_doi(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("ra_crossref.json"))
    answer = await client.agency("10.1038/nature12373")
    assert answer.DOI == "10.1038/nature12373"
    assert answer.RA == "Crossref"
    assert answer.status is None
    assert last_request(httpx_mock).url.path == "/ra/10.1038/nature12373"


async def test_agency_accepts_doi_urls(client, httpx_mock):
    httpx_mock.add_response(json=load_fixture("ra_datacite.json"))
    answer = await client.agency("https://doi.org/10.5281/zenodo.1238808")
    assert answer.RA == "DataCite"
    assert last_request(httpx_mock).url.path == "/ra/10.5281/zenodo.1238808"


async def test_agencies_of_many_dois(client, httpx_mock):
    httpx_mock.add_response(json=PAIR)
    answers = await client.agencies(["10.1038/nature12373", "10.5281/zenodo.1238808"])
    assert [answer.RA for answer in answers] == ["Crossref", "DataCite"]


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


@pytest.mark.parametrize("value", [[]])
async def test_agencies_rejects_empty_input(client, httpx_mock, value):
    with pytest.raises(ConfigurationError, match="at least one"):
        await client.agencies(value)
    assert not httpx_mock.get_requests()


async def test_agencies_sends_invalid_strings_for_the_status_answer(client, httpx_mock):
    """``/ra/`` answers malformed strings itself; nothing is rejected client-side."""
    httpx_mock.add_response(json=INVALID)
    answer = (await client.agencies(["https://doi.org/not-a-doi"]))[0]
    assert answer.DOI == "not-a-doi"
    assert answer.status == "Invalid DOI"
    assert httpx_mock.get_requests()[0].url.path == "/ra/not-a-doi"


async def test_agencies_raises_on_non_list_body(client, httpx_mock):
    httpx_mock.add_response(json={"unexpected": True})
    with pytest.raises(ConfigurationError, match="non-list"):
        await client.agency("10.1038/nature12373")
