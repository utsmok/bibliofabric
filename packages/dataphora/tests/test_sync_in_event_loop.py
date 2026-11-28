"""The sync client works when called from inside a running event loop.

Lives outside ``tests/_async/`` on purpose: it only makes sense for the sync
variant, so the generator does not copy it.
"""

import asyncio

from dataphora import DataphoraSyncClient

from .conftest import doi_resource, envelope


def test_sync_client_inside_running_loop(httpx_mock, settings):
    httpx_mock.add_response(
        json=envelope([doi_resource("10.5438/0012")], total=143184779)
    )
    httpx_mock.add_response(json=envelope([doi_resource("10.5438/0007")], total=450))

    async def main():
        assert asyncio.get_running_loop()  # we really are on a loop
        with DataphoraSyncClient(settings=settings) as client:
            page = client.dois.search()
            filtered = client.dois.search({"resource-type-id": "dataset"})
        return page.results[0].doi, filtered.total

    first_doi, total = asyncio.run(main())
    assert first_doi == "10.5438/0012"
    assert total == 450
    paths = [r.url.path for r in httpx_mock.get_requests()]
    assert paths == ["/dois", "/dois"]
    assert httpx_mock.get_requests()[1].url.params["resource-type-id"] == "dataset"
