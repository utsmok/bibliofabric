"""Variant-specific client fixtures.

The generator renames ``ScholiastClient`` to
``ScholiastSyncClient`` in the generated ``tests/_sync`` twin, so
each variant builds its own client here.
"""

import pytest
from scholiast import ScholiastClient


@pytest.fixture
async def client(settings):
    async with ScholiastClient(settings=settings) as s2_client:
        yield s2_client
