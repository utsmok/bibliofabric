"""Request-class limiter and run_bounded behavior, per the sync contract."""

import httpx
import pytest
from bibliofabric._async import _concurrency
from bibliofabric.exceptions import NetworkError

from .conftest import FakeSettings


async def test_per_class_intervals_are_independent(monkeypatch):
    sleeps: list[float] = []
    clock = [100.0]
    monkeypatch.setattr(_concurrency, "_now", lambda: clock[0])

    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        clock[0] += seconds

    monkeypatch.setattr(_concurrency, "sleep", fake_sleep)
    limiter = _concurrency.Limiter({"single": 10.0, "list": 3.0}, max_concurrency=5)
    await limiter.acquire("single")
    limiter.release()
    await limiter.acquire("single")
    limiter.release()
    assert sleeps == [pytest.approx(0.1)]

    # A different class is paced on its own timeline and never waits for the
    # single class's gate.
    await limiter.acquire("list")
    limiter.release()
    assert sleeps == [pytest.approx(0.1)]
    await limiter.acquire("list")
    limiter.release()
    assert sleeps == [pytest.approx(0.1), pytest.approx(1 / 3)]

    # Elapsed wall time frees the gate without sleeping.
    clock[0] += 1.0
    await limiter.acquire("single")
    limiter.release()
    assert sleeps == [pytest.approx(0.1), pytest.approx(1 / 3)]


async def test_default_class_uses_max_requests_per_second(monkeypatch):
    sleeps: list[float] = []
    clock = [0.0]
    monkeypatch.setattr(_concurrency, "_now", lambda: clock[0])

    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        clock[0] += seconds

    monkeypatch.setattr(_concurrency, "sleep", fake_sleep)
    limiter = _concurrency.Limiter(
        {"default": 2.0, "unlimited": None}, max_concurrency=5
    )

    await limiter.acquire()
    limiter.release()
    await limiter.acquire()
    limiter.release()
    # Undeclared class falls back to "default".
    await limiter.acquire("unknown")
    limiter.release()
    # Explicit None disables spacing for that class.
    await limiter.acquire("unlimited")
    limiter.release()
    await limiter.acquire("unlimited")
    limiter.release()
    assert sleeps == [pytest.approx(0.5), pytest.approx(0.5)]


async def test_waiting_class_does_not_starve_other_class_concurrency():
    # Two slow "list" callers sleep on their pacing gate; a concurrent "single"
    # caller must still obtain the lone concurrency slot without waiting for
    # the sleeping "list" callers.
    limiter = _concurrency.Limiter({"list": 2.0, "single": 100.0}, max_concurrency=1)
    order: list[str] = []

    async def call(label: str) -> None:
        rate_class = "list" if label.startswith("list") else "single"
        await limiter.acquire(rate_class)
        try:
            order.append(label)
            await _concurrency.sleep(0.02)
        finally:
            limiter.release()

    await _concurrency.run_bounded(call, ["list-1", "list-2", "single-1"], 3)
    assert order.index("single-1") < order.index("list-2")


async def test_shared_concurrency_across_classes():
    limiter = _concurrency.Limiter({"a": 10.0, "b": 10.0}, max_concurrency=2)
    inflight = 0
    peak = 0

    async def call(rate_class: str) -> None:
        nonlocal inflight, peak
        await limiter.acquire(rate_class)
        inflight += 1
        peak = max(peak, inflight)
        await _concurrency.sleep(0.05)
        inflight -= 1
        limiter.release()

    await _concurrency.run_bounded(call, ["a", "a", "b", "b", "a", "b"], 6)
    assert peak == 2


async def test_run_bounded_preserves_order_and_raises_first_error():
    async def work(item: int) -> int:
        await _concurrency.sleep(0.01)
        if item == 3:
            raise ValueError("boom")
        return item * 10

    assert await _concurrency.run_bounded(work, [], 2) == []
    assert await _concurrency.run_bounded(work, [1, 2, 4], 2) == [10, 20, 40]
    with pytest.raises(ValueError, match="boom"):
        await _concurrency.run_bounded(work, [1, 3, 4], 2)
    with pytest.raises(ValueError, match="positive"):
        await _concurrency.run_bounded(work, [1], 0)
    with pytest.raises(ValueError, match="positive"):
        _concurrency.Limiter({}, max_concurrency=0)


async def test_limiter_release_on_send_failure(httpx_mock, make_client):
    """A failing send must give its concurrency slot back."""
    httpx_mock.add_exception(httpx.ConnectError("boom"), url="https://fake.test/api/x")
    client = make_client(settings=FakeSettings(max_retries=0, max_concurrency=1))
    with pytest.raises(NetworkError):
        await client.request("GET", "x")
    # The slot was released: a follow-up request does not deadlock.
    httpx_mock.add_response(url="https://fake.test/api/y", json={})
    await client.request("GET", "y")
