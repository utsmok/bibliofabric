"""The sync client works when called from inside a running event loop.

Lives outside ``tests/_async/`` on purpose: it only makes sense for the sync
variant, so the generator does not copy it.
"""

import asyncio

from aletheca import AlethecaSyncClient

from .conftest import entity, envelope


def test_sync_client_inside_running_loop(httpx_mock, settings):
    httpx_mock.add_response(json=entity("W1234567890"))
    httpx_mock.add_response(json=envelope([entity("W2741809807")], count=1))

    async def main():
        assert asyncio.get_running_loop()  # we really are on a loop
        with AlethecaSyncClient(settings=settings) as client:
            work = client.works.get("W1234567890")
            page = client.works.search(select=["id"])
        return work.id, page.total

    work_id, total = asyncio.run(main())
    assert work_id == entity("W1234567890")["id"]
    assert total == 1
    paths = [r.url.path for r in httpx_mock.get_requests()]
    assert paths == ["/works/W1234567890", "/works"]
