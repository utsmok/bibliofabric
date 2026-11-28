"""The sync client works when called from inside a running event loop.

Lives outside ``tests/_async/`` on purpose: it only makes sense for the sync
variant, so the generator does not copy it.
"""

import asyncio

from prodromus import ProdromusSyncClient

from .conftest import load_fixture


def test_sync_client_inside_running_loop(httpx_mock, settings):
    httpx_mock.add_response(json=load_fixture("details_doi.json"))

    async def main():
        assert asyncio.get_running_loop()
        with ProdromusSyncClient(settings=settings) as client:
            return client.details.get("10.1101/339747")

    versions = asyncio.run(main())
    assert len(versions) == 4
