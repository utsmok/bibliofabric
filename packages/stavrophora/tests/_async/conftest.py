"""Async-variant fixtures; ``tests/_sync`` gets the generated sync twins."""

import pytest
from stavrophora import StavrophoraClient, StavrophoraSettings

from ..conftest import fixture, work, works_envelope  # noqa: F401  re-exported


@pytest.fixture
def settings() -> StavrophoraSettings:
    # max_requests_per_second=None skips the pacing gate so mocked tests stay fast
    return StavrophoraSettings(
        mailto="tester@example.org", max_requests_per_second=None, max_concurrency=8
    )


@pytest.fixture
async def client(settings):
    async with StavrophoraClient(settings=settings) as client:
        yield client
