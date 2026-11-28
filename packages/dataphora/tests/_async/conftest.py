"""Variant-specific client fixtures.

The generator renames ``DataphoraClient`` to ``DataphoraSyncClient`` in
the generated ``tests/_sync`` twin, so each variant builds its own client
here.
"""

import pytest
from dataphora import DataphoraClient


@pytest.fixture
async def client(settings):
    async with DataphoraClient(settings=settings) as datacite_client:
        yield datacite_client
