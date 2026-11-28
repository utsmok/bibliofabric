"""Variant-specific client fixtures.

The generator renames ``DiurnaliaClient`` to ``DiurnaliaSyncClient`` in the
generated ``tests/_sync`` twin, so each variant builds its own client here.
"""

import pytest
from diurnalia import DiurnaliaClient


@pytest.fixture
async def client(settings):
    async with DiurnaliaClient(settings=settings) as doaj_client:
        yield doaj_client
