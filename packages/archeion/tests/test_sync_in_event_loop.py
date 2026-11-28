"""The sync client works when called from inside a running event loop.

Lives outside ``tests/_async/`` on purpose: it only makes sense for the sync
variant, so the generator does not copy it.
"""

import asyncio

from archeion import ArcheionSyncClient

from .conftest import load_fixture


def test_sync_client_inside_running_loop(httpx_mock, settings):
    httpx_mock.add_response(text=load_fixture("two_entries.xml"))

    async def main():
        assert asyncio.get_running_loop()
        with ArcheionSyncClient(settings=settings) as client:
            return client.query.batch_get(["1706.03762", "hep-th/9711200"])

    found = asyncio.run(main())
    assert sorted(found) == ["1706.03762", "hep-th/9711200"]
