"""Async client fixture; the generator renames the class in tests/_sync/."""

import pytest
from quiddita import QuidditaClient


@pytest.fixture
async def client(settings):
    async with QuidditaClient(settings=settings) as wikidata_client:
        yield wikidata_client
