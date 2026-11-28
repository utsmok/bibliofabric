"""Variant-specific client fixtures.

The generator renames ``ZenothecaClient`` to ``ZenothecaSyncClient`` in the
generated ``tests/_sync`` twin, so each variant builds its own client here.
"""

import pytest
from zenotheca import ZenothecaClient


@pytest.fixture
async def client(settings):
    async with ZenothecaClient(settings=settings) as zenodo_client:
        yield zenodo_client
