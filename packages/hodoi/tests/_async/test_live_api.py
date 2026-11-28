"""Live DOI System smoke tests against doi.org.

Deselected by default; run with ``pytest -m live_api``. The proxy needs no
credentials. Each test fetches the same real records its fixture in
``tests/fixtures`` was trimmed from.
"""

import bibliofabric
import pytest
from hodoi import (
    BIBTEX,
    CSL_JSON,
    DATACITE_JSON,
    RIS,
    SCHEMAORG_JSONLD,
    UNIXREF_XML,
    HodoiClient,
    HodoiSettings,
    NotFoundError,
)

pytestmark = pytest.mark.live_api

CROSSREF_DOI = "10.1038/nature12373"
DATACITE_DOI = "10.5281/zenodo.1238808"
MEDRA_DOI = "10.1400/56174"
LANDING = "https://www.nature.com/articles/nature12373"


@pytest.fixture
async def live_client():
    async with HodoiClient(settings=HodoiSettings(_env_file=None)) as client:
        yield client


async def test_agency_smoke(live_client):
    answers = await live_client.agencies([CROSSREF_DOI, DATACITE_DOI, MEDRA_DOI])
    assert [answer.RA for answer in answers] == ["Crossref", "DataCite", "mEDRA"]


async def test_agency_unknown_doi_smoke(live_client):
    answer = await live_client.agency("10.9999/nope")
    assert answer.RA is None
    assert answer.status == "DOI does not exist"


async def test_handle_smoke(live_client):
    record = await live_client.handle(CROSSREF_DOI)
    assert record.responseCode == 1
    assert record.handle == CROSSREF_DOI
    assert any(value.type == "URL" for value in record.values)


async def test_handle_filters_smoke(live_client):
    record = await live_client.handle(CROSSREF_DOI, type="URL")
    assert [value.type for value in record.values] == ["URL"]


async def test_handle_not_found_smoke(live_client):
    with pytest.raises(NotFoundError):
        await live_client.handle("10.9999/nope")


async def test_landing_url_smoke(live_client):
    assert await live_client.landing_url(CROSSREF_DOI) == LANDING


async def test_content_crossref_csl_smoke(live_client):
    item = await live_client.content(CROSSREF_DOI, CSL_JSON)
    assert isinstance(item.title, str) and item.title
    assert item.DOI == CROSSREF_DOI


async def test_content_datacite_smoke(live_client):
    record = await live_client.content(DATACITE_DOI, DATACITE_JSON)
    assert record.doi and record.doi.lower() == DATACITE_DOI
    thing = await live_client.content(DATACITE_DOI, SCHEMAORG_JSONLD)
    assert thing.type == "SoftwareSourceCode"


async def test_content_text_representations_smoke(live_client):
    bib = await live_client.content(CROSSREF_DOI, BIBTEX)
    assert bib.strip().startswith("@article")
    ris = await live_client.content(CROSSREF_DOI, RIS)
    assert ris.startswith("TY  - JOUR")


async def test_content_unsupported_type_smoke(live_client):
    with pytest.raises(bibliofabric.exceptions.APIError):
        await live_client.content(DATACITE_DOI, UNIXREF_XML)


async def test_raw_redirect_smoke(live_client):
    payload = await live_client.raw(CROSSREF_DOI, CSL_JSON)
    assert b"Handle Redirect" in payload
