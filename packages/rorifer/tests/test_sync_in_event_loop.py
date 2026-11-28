"""The sync client works when called from inside a running event loop.

Lives outside ``tests/_async/`` on purpose: it only makes sense for the sync
variant, so the generator does not copy it.
"""

import asyncio

from rorifer import RoriferSyncClient

from .conftest import envelope, organization


def test_sync_client_inside_running_loop(httpx_mock, settings):
    httpx_mock.add_response(json=organization("006hf6230"))
    httpx_mock.add_response(json=envelope([organization("021nxhr62")]))

    async def main():
        assert asyncio.get_running_loop()  # we really are on a loop
        with RoriferSyncClient(settings=settings) as client:
            record = client.organizations.get("006hf6230")
            page = client.organizations.search(query="nsf")
        return record.id, page.total

    record_id, total = asyncio.run(main())
    assert record_id == "https://ror.org/006hf6230"
    assert total == 1
    paths = [r.url.path for r in httpx_mock.get_requests()]
    assert paths == ["/v2/organizations/006hf6230", "/v2/organizations"]
