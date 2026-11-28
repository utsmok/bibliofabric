"""The sync client works when called from inside a running event loop.

Lives outside ``tests/_async/`` on purpose: it only makes sense for the sync
variant, so the generator does not copy it.
"""

import asyncio

from diurnalia import DiurnaliaSyncClient

from .conftest import article, envelope, journal


def test_sync_client_inside_running_loop(httpx_mock, settings):
    httpx_mock.add_response(
        json=envelope([journal("2fdf1470373343b7bd4f825179c685f5")])
    )
    httpx_mock.add_response(
        json=envelope([article("57dfae3d0df24509a5f65fc0498f72fc")])
    )

    async def main():
        assert asyncio.get_running_loop()  # we really are on a loop
        with DiurnaliaSyncClient(settings=settings) as client:
            record = client.journals.get("1932-6203")
            page = client.articles.search(query="doi:10.3389/fpubh.2020.00115")
        return record, page

    record, page = asyncio.run(main())
    assert record.title == "Journal 2fdf1470373343b7bd4f825179c685f5"
    assert page.results[0].doi == "10.3389/fpubh.2020.00115"
    paths = [r.url.path for r in httpx_mock.get_requests()]
    assert paths == [
        "/api/v4/search/journals/issn:1932-6203",
        "/api/v4/search/articles/doi:10.3389/fpubh.2020.00115",
    ]
