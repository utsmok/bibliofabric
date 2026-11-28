"""Variant-specific client fixtures.

The generator renames ``OrchisClient`` to ``OrchisSyncClient`` in the
generated ``tests/_sync`` twin, so each variant builds its own client here.
"""

import pytest
from orchis import OrchisClient


@pytest.fixture
async def client(settings):
    async with OrchisClient(settings=settings) as orcid_client:
        yield orcid_client
