"""Live Semantic Scholar smoke tests against the real API.

Deselected by default; run with ``pytest -m live_api``. The tests need no
API key: they run on the shared anonymous pool, which is contended and
answers HTTP 429 often, so every test skips on a rate limit instead of
failing. Each test makes at most one or two requests.
"""

from collections.abc import Callable
from time import sleep
from typing import NoReturn, cast

import pytest
from bibliofabric.exceptions import RateLimitError
from scholiast import (
    NotFoundError,
    ScholiastClient,
    ScholiastSettings,
)

pytestmark = pytest.mark.live_api

DOI = "DOI:10.1038/nature12373"


# The installed pytest type stubs disagree with the runtime signature of
# pytest.skip about its positional argument, so the attribute goes through a
# callable cast.
_skip = cast(Callable[..., NoReturn], pytest.skip)


def skip_rate_limited() -> None:
    _skip("rate limited")


@pytest.fixture
async def live_client():
    async with ScholiastClient(
        settings=ScholiastSettings(_env_file=None, api_key=None)
    ) as client:
        yield client


def pace() -> None:
    """Keep at most 1 request per second between tests."""
    sleep(1.05)


async def test_get_paper_smoke(live_client):
    pace()
    try:
        paper_record = await live_client.papers.get(
            DOI, select=["title", "year", "citationCount", "externalIds"]
        )
    except RateLimitError:
        skip_rate_limited()
    assert paper_record.paperId
    assert paper_record.title == "Nanometer scale thermometry in a living cell"
    assert paper_record.externalIds is not None
    assert paper_record.externalIds.DOI == "10.1038/nature12373"


async def test_paper_batch_smoke(live_client):
    pace()
    try:
        papers = await live_client.papers.batch(
            [DOI, "DOI:10.9999/does-not-exist"], fields=["title"]
        )
    except RateLimitError:
        skip_rate_limited()
    assert len(papers) == 1


async def test_citations_smoke(live_client):
    pace()
    try:
        citations = await live_client.papers.citations(
            DOI, fields=["title", "isInfluential"], limit=5
        )
    except RateLimitError:
        skip_rate_limited()
    assert citations.results
    assert citations.results[0].citingPaper is not None


async def test_recommendations_smoke(live_client):
    pace()
    try:
        papers = await live_client.recommendations.for_paper(DOI, limit=5)
    except RateLimitError:
        skip_rate_limited()
    assert papers
    assert papers[0].paperId


async def test_dataset_releases_smoke(live_client):
    pace()
    try:
        releases = await live_client.datasets.releases()
    except RateLimitError:
        skip_rate_limited()
    assert releases
    assert releases[0].startswith("20")


async def test_get_not_found_smoke(live_client):
    pace()
    try:
        await live_client.papers.get("DOI:10.9999/this-does-not-exist-0000")
    except RateLimitError:
        skip_rate_limited()
    except NotFoundError:
        return
    raise AssertionError("expected NotFoundError for an unknown DOI")
