"""The sync client works when called from inside a running event loop.

Lives outside ``tests/_async/`` on purpose: it only makes sense for the sync
variant, so the generator does not copy it.
"""

import asyncio

from hodoi import HodoiSyncClient

from .conftest import load_fixture


def test_sync_client_inside_running_loop(httpx_mock, settings):
    httpx_mock.add_response(json=load_fixture("ra_crossref.json"))
    httpx_mock.add_response(json=load_fixture("handle_crossref.json"))

    async def main():
        assert asyncio.get_running_loop()  # we really are on a loop
        with HodoiSyncClient(settings=settings) as client:
            answer = client.agency("10.1038/nature12373")
            record = client.handle("10.1038/nature12373")
        return answer.RA, record.handle

    agency, handle = asyncio.run(main())
    assert agency == "Crossref"
    assert handle == "10.1038/nature12373"
    paths = [r.url.path for r in httpx_mock.get_requests()]
    assert paths == ["/ra/10.1038/nature12373", "/api/handles/10.1038/nature12373"]
