"""The sync client must work when called from inside a running event loop."""

import asyncio

from stavrophora import StavrophoraSettings, StavrophoraSyncClient

from .conftest import fixture


def test_sync_client_inside_running_loop(httpx_mock):
    httpx_mock.add_response(json=fixture("work_get.json"))
    settings = StavrophoraSettings(
        mailto="tester@example.org", max_requests_per_second=None
    )

    async def main() -> str:
        with StavrophoraSyncClient(settings=settings) as client:
            fetched = await asyncio.to_thread(client.works.get, "10.1038/nature12373")
            return fetched.doi

    assert asyncio.run(main()) == "10.1038/nature12373"
