"""Variant-specific client fixtures.

The generator renames ``HodoiClient`` to ``HodoiSyncClient`` in the
generated ``tests/_sync`` twin, so each variant builds its own client here.
"""

import pytest
from hodoi import HodoiClient


@pytest.fixture
async def client(settings):
    async with HodoiClient(settings=settings) as doi_client:
        yield doi_client
