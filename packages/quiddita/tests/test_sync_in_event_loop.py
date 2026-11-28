"""The sync client works when called from inside a running event loop.

Lives outside ``tests/_async/`` on purpose: it only makes sense for the sync
variant, so the generator does not copy it.
"""

import asyncio

from quiddita import QuidditaSyncClient

from .conftest import entities_envelope, entity


def test_sync_client_inside_running_loop(httpx_mock, settings):
    httpx_mock.add_response(json=entities_envelope(entity()))
    httpx_mock.add_response(json=entities_envelope(entity("P31"), entity()))

    async def main():
        assert asyncio.get_running_loop()  # we really are on a loop
        with QuidditaSyncClient(settings=settings) as client:
            record = client.entities.get("Q42")
            batch = client.entities.batch_get(["Q42", "P31"])
        return record.id, sorted(batch)

    record_id, ids = asyncio.run(main())
    assert record_id == "Q42"
    assert ids == ["P31", "Q42"]
