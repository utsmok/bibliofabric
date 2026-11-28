"""The sync client works when called from inside a running event loop.

Lives outside ``tests/_async/`` on purpose: it only makes sense for the sync
variant, so the generator does not copy it.
"""

import asyncio

from europaea import EuropaeaSyncClient

from .conftest import lite_record, search_envelope


def test_sync_client_inside_running_loop(httpx_mock, settings):
    httpx_mock.add_response(json=search_envelope([lite_record()], hit_count=1))

    async def main():
        assert asyncio.get_running_loop()  # we really are on a loop
        with EuropaeaSyncClient(settings=settings) as client:
            page = client.search.search(query="cancer", result_type="lite")
        return page.total, page.results[0].id

    total, record_id = asyncio.run(main())
    assert total == 1
    assert record_id == "23903748"
    paths = [r.url.path for r in httpx_mock.get_requests()]
    assert paths == ["/europepmc/webservices/rest/search"]
