"""Variant-specific client fixtures.

The generator renames ``SeriatimClient`` to ``SeriatimSyncClient`` in the
generated ``tests/_sync`` twin, so each variant builds its own client here.
"""

import pytest
from seriatim import SeriatimClient


@pytest.fixture
async def client(settings):
    async with SeriatimClient(settings=settings) as issn_client:
        yield issn_client
