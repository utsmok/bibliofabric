"""Variant-specific client fixtures.

The generator renames ``RoriferClient`` to ``RoriferSyncClient`` in the
generated ``tests/_sync`` twin, so each variant builds its own client here.
"""

import pytest
from rorifer import RoriferClient


@pytest.fixture
async def client(settings):
    async with RoriferClient(settings=settings) as ror_client:
        yield ror_client
