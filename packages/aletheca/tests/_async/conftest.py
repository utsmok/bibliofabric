"""Variant-specific client fixtures.

The generator renames ``AlethecaClient`` to ``AlethecaSyncClient`` in the
generated ``tests/_sync`` twin, so each variant builds its own client here.
"""

import pytest
from aletheca import AlethecaClient


@pytest.fixture
async def client(settings):
    async with AlethecaClient(settings=settings) as aletheca_client:
        yield aletheca_client
