"""Variant-specific client fixtures.

The generator renames ``OpcitatoClient`` to ``OpcitatoSyncClient``
in the generated ``tests/_sync`` twin, so each variant builds its own client
here.
"""

import pytest
from opcitato import OpcitatoClient


@pytest.fixture
async def client(settings):
    async with OpcitatoClient(settings=settings) as opencitations_client:
        yield opencitations_client
