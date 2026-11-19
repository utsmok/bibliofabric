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
    ``None`` or a non-positive rate disables spacing for that class.
    :meth:`acquire` claims a concurrency slot, then claims the class's next
    slot on a shared monotonic timeline. The gate lock is only held to book
    the slot, so callers of one class never block callers of another.
    """

    def __init__(
        self, rate_limits: Mapping[str, float | None], max_concurrency: int
    ) -> None:
        self._min_intervals = {
            name: 1.0 / rate
            for name, rate in rate_limits.items()
            if rate is not None and rate > 0
        }
        self._slots = asyncio.Semaphore(max_concurrency)
        self._gates: dict[str, asyncio.Lock] = {}
        self._next_slot: dict[str, float] = {}

    async def acquire(self, rate_class: str = "default") -> None:
        """Take one concurrency slot and wait for the class's next slot."""
        await self._slots.acquire()
        interval = self._min_intervals.get(rate_class)
        if interval is None:
            return
        try:
            while True:
                gate = self._gates.setdefault(rate_class, asyncio.Lock())
                async with gate:
                    wait = self._next_slot.get(rate_class, 0.0) - _now()
                    if wait <= 0:
                        self._next_slot[rate_class] = _now() + interval
                        return
                await sleep(wait)
        except BaseException:
            self._slots.release()
            raise

    def release(self) -> None:
        """Give back the concurrency slot taken by :meth:`acquire`."""
        self._slots.release()


async def maybe_await(value: Any) -> Any:
    """Await ``value`` when it is awaitable, else return it unchanged."""
    if inspect.isawaitable(value):
        return await value
    return value


async def run_bounded[T](
    fn: Callable[[T], Awaitable[Any]],
    items: Sequence[T],
    concurrency: int,
) -> list[Any]:
    """Run ``fn`` over ``items`` with at most ``concurrency`` tasks in flight.

    Results keep the input order; the first failure re-raises.
    """
    semaphore = asyncio.Semaphore(concurrency)

    async def run(item: T) -> Any:
        async with semaphore:
            return await fn(item)

    return list(await asyncio.gather(*(run(item) for item in items)))
