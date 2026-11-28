"""The sync client works when called from inside a running event loop.

Lives outside ``tests/_async/`` on purpose: it only makes sense for the sync
variant, so the generator does not copy it.
"""

import asyncio

from scholiast import ScholiastSyncClient

from .conftest import paper, search_envelope


def test_sync_client_inside_running_loop(httpx_mock, settings):
    httpx_mock.add_response(json=paper("a5de30adc5c22bc86e8cfabe7fbd07c052d196a8"))
    httpx_mock.add_response(json=search_envelope([paper("f712fab0d58ae6492e3")]))

    async def main():
        assert asyncio.get_running_loop()  # we really are on a loop
        with ScholiastSyncClient(settings=settings) as client:
            record = client.papers.get("DOI:10.1038/nature12373")
            page = client.papers.search(query="photosynthesis")
        return record.paperId, page.total

    paper_id, total = asyncio.run(main())
    assert paper_id == "a5de30adc5c22bc86e8cfabe7fbd07c052d196a8"
    assert total == 1
    requests = httpx_mock.get_requests()
    assert [r.url.path for r in requests] == [
        "/graph/v1/paper/DOI:10.1038/nature12373",
        "/graph/v1/paper/search",
    ]
