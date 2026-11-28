"""Variant-specific client fixtures.

The generator renames ``EuropaeaClient`` to ``EuropaeaSyncClient`` in
the generated ``tests/_sync`` twin, so each variant builds its own client.
"""

import pytest
from europaea import EuropaeaClient


@pytest.fixture
async def client(settings):
    async with EuropaeaClient(settings=settings) as europepmc_client:
        yield europepmc_client
