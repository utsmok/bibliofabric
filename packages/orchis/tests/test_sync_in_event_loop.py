"""The sync client works when called from inside a running event loop.

Lives outside ``tests/_async/`` on purpose: it only makes sense for the sync
variant, so the generator does not copy it.
"""

import asyncio

from orchis import OrchisSyncClient

from .conftest import ORCID_ID, expanded_envelope, expanded_result, load_fixture


def test_sync_client_inside_running_loop(httpx_mock, settings):
    httpx_mock.add_response(json=load_fixture("record.json"))
    httpx_mock.add_response(json=expanded_envelope([expanded_result(ORCID_ID)]))

    async def main():
        assert asyncio.get_running_loop()  # we really are on a loop
        with OrchisSyncClient(settings=settings) as client:
            record = client.record.get(ORCID_ID)
            page = client.expanded_search.search(
                query="family-name:Kucsko", page_size=2
            )
        identifier = record.orcid_identifier
        assert identifier is not None
        return identifier.path, page.total

    record_id, total = asyncio.run(main())
    assert record_id == ORCID_ID
    assert total == 1
    paths = [r.url.path for r in httpx_mock.get_requests()]
    assert paths == [f"/v3.0/{ORCID_ID}/record", "/v3.0/expanded-search/"]
