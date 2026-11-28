"""Variant-specific client fixtures.

The generator renames ``ProdromusClient`` to ``ProdromusSyncClient`` in the
generated ``tests/_sync`` twin, so each variant builds its own client here.
"""

import pytest
from prodromus import ProdromusClient


@pytest.fixture
async def client(settings):
    async with ProdromusClient(settings=settings) as biorxiv_client:
        yield biorxiv_client
