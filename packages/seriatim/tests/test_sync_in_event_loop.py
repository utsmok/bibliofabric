"""The sync client works when called from inside a running event loop.

Lives outside ``tests/_async/`` on purpose: it only makes sense for the sync
variant, so the generator does not copy it.
"""

import asyncio

from seriatim import SeriatimSyncClient

from .conftest import load_fixture, load_json_fixture


def test_sync_client_inside_running_loop(httpx_mock, settings):
    httpx_mock.add_response(json=load_json_fixture("record_print_nature.json"))
    httpx_mock.add_response(json=load_json_fixture("issn_l_nature.json"))
    httpx_mock.add_response(text=load_fixture("search_results.html"))

    async def main():
        assert asyncio.get_running_loop()  # we really are on a loop
        with SeriatimSyncClient(settings=settings) as client:
            record = client.records.get("0028-0836")
            cluster = client.issn_l.get("0028-0836")
            page = client.search.page("0028-0836")
        return record.issn, cluster.issn_l, page.total

    record_issn, issn_l_value, total = asyncio.run(main())
    assert record_issn == "0028-0836"
    assert issn_l_value == "0028-0836"
    assert total == 6
    paths = [r.url.path for r in httpx_mock.get_requests()]
    assert paths == [
        "/resource/ISSN/0028-0836",
        "/resource/ISSN-L/0028-0836",
        "/search",
    ]
