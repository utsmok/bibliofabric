"""The sync client works when called from inside a running event loop.

Lives outside ``tests/_async/`` on purpose: it only makes sense for the sync
variant, so the generator does not copy it.
"""

import asyncio

from opcitato import OpcitatoSyncClient

from .conftest import citation, count_rows


def test_sync_client_inside_running_loop(httpx_mock, settings):
    httpx_mock.add_response(json=[citation()])
    httpx_mock.add_response(json=count_rows(57))

    async def main():
        assert asyncio.get_running_loop()  # we really are on a loop
        with OpcitatoSyncClient(settings=settings) as client:
            rows = client.index.citations("doi:10.1108/jd-12-2013-0166")
            count = client.index.citation_count("doi:10.1108/jd-12-2013-0166")
        return rows[0].oci, count

    oci, count = asyncio.run(main())
    assert oci == "06101801781-06180334099"
    assert count == 57
    paths = [r.url.path for r in httpx_mock.get_requests()]
    assert paths == [
        "/index/v2/citations/doi:10.1108/jd-12-2013-0166",
        "/index/v2/citation-count/doi:10.1108/jd-12-2013-0166",
    ]
