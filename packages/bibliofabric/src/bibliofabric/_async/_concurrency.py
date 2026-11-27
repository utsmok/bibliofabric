"""Async I/O primitives for the ``_async`` modules.

``scripts/unasync.py`` turns ``_async`` modules into their sync twins
(``bibliofabric._sync``); the sync twin of this module is hand-written and
excluded from generation. I/O code imports everything async-specific from
here and never from ``asyncio`` directly, so token replacement is all the
generator has to do.
"""

import asyncio
import inspect
import time
from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Any

sleep = asyncio.sleep
"""Pacing sleep; the sync twin replaces it with ``time.sleep``."""

Lock = asyncio.Lock
"""Mutex; the sync twin replaces it with ``threading.Lock``."""


def _now() -> float:
    """Monotonic clock used for pacing."""
    return time.monotonic()


class Limiter:
    """Per-class minimum-interval gates under one shared concurrency bound.

    ``rate_limits`` maps a class name to its allowed requests per second;
    ``None`` or a non-positive rate disables spacing for that class. Undeclared
    rate classes fall back to ``"default"``. :meth:`acquire` reserves the
    class's next slot on a shared monotonic timeline, sleeps outside the lock
    before taking a concurrency slot (so waiting callers of one class never
    starve another class's concurrency slots), and then claims a concurrency
    slot.
    """

    def __init__(
        self, rate_limits: Mapping[str, float | None], max_concurrency: int
    ) -> None:
        if max_concurrency <= 0:
            raise ValueError(
                f"max_concurrency must be positive, got {max_concurrency}."
            )
        self._intervals: dict[str, float | None] = {
            name: (1.0 / rate if rate is not None and rate > 0 else None)
            for name, rate in rate_limits.items()
        }
        self._slots = asyncio.Semaphore(max_concurrency)
        self._gates: dict[str, asyncio.Lock] = {
            name: asyncio.Lock()
            for name, interval in self._intervals.items()
            if interval is not None
        }
        self._next_slot: dict[str, float] = {}

    async def acquire(self, rate_class: str = "default") -> None:
        """Wait for the class's next pacing slot, then claim a concurrency slot."""
        if rate_class in self._intervals:
            effective_class = rate_class
            interval = self._intervals[rate_class]
        else:
            effective_class = "default"
            interval = self._intervals.get("default")

        if interval is not None:
            gate = self._gates[effective_class]
            async with gate:
                now = _now()
                slot = max(now, self._next_slot.get(effective_class, float("-inf")))
                self._next_slot[effective_class] = slot + interval
            wait = slot - now
            if wait > 0:
                await sleep(wait)

        await self._slots.acquire()

    def release(self) -> None:
        """Give back the concurrency slot taken by :meth:`acquire`."""
        self._slots.release()


async def maybe_await(value: Any) -> Any:
    """Await ``value`` when it is awaitable, else return it unchanged."""
    if inspect.isawaitable(value):
        return await value
    return value


async def run_bounded[T, R](
    fn: Callable[[T], Awaitable[R]],
    items: Sequence[T],
    concurrency: int,
) -> list[R]:
    """Run ``fn`` over ``items`` with at most ``concurrency`` tasks in flight.

    Results keep the input order; the first failure cancels remaining sibling
    tasks and re-raises.
    """
    if concurrency <= 0:
        raise ValueError(f"concurrency must be positive, got {concurrency}.")
    if not items:
        return []
    semaphore = asyncio.Semaphore(concurrency)

    async def run(item: T) -> R:
        async with semaphore:
            return await fn(item)

    tasks = [asyncio.create_task(run(item)) for item in items]
    try:
        return list(await asyncio.gather(*tasks))
    except BaseException:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise
