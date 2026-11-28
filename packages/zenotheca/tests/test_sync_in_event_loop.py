"""The sync client works when called from inside a running event loop.

Lives outside ``tests/_async/`` on purpose: it only makes sense for the sync
variant, so the generator does not copy it.
"""

import asyncio

from zenotheca import ZenothecaSyncClient

from .conftest import RECORD_ID, community, envelope, record


def test_sync_client_inside_running_loop(httpx_mock, settings):
    httpx_mock.add_response(json=record())
    httpx_mock.add_response(json=envelope([community()], total=8978))

    async def main():
        assert asyncio.get_running_loop()  # we really are on a loop
        with ZenothecaSyncClient(settings=settings) as client:
            got = client.records.get(RECORD_ID)
            page = client.communities.search(query="data curation")
        return got.id, page.total

    record_id, total = asyncio.run(main())
    assert record_id == RECORD_ID
    assert total == 8978
    paths = [r.url.path for r in httpx_mock.get_requests()]
    assert paths == [f"/api/records/{RECORD_ID}", "/api/communities"]
