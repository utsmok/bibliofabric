"""Variant-specific client fixtures.

The generator renames ``ArcheionClient`` to ``ArcheionSyncClient`` in the
generated ``tests/_sync`` twin, so each variant builds its own client here.
"""

import pytest
from archeion import ArcheionClient


@pytest.fixture
async def client(settings):
    async with ArcheionClient(settings=settings) as arxiv_client:
        yield arxiv_client
