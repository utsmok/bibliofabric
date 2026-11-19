"""Sync twins of ``bibliofabric._async._concurrency``.

Hand-written and excluded from generation, like its async counterpart. This
module never touches an event loop: plain ``time.sleep``, ``threading``
locks, and a thread pool for bounded batch calls.
"""

import threading
import time
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from typing import Any

sleep = time.sleep
"""Pacing sleep."""

Lock = threading.Lock
"""Mutex."""


def _now() -> float:
    """Monotonic clock used for pacing."""
    return time.monotonic()


class Limiter:
    """Per-class minimum-interval gates under one shared concurrency bound.

    Thread-safe twin of the async limiter with the same behavior: one
    minimum-interval gate per class, booked on a shared monotonic timeline,
    and one shared concurrency bound. The gate lock is only held to book the
    slot, so callers of one class never block callers of another.
    """

    def __init__(
        self, rate_limits: Mapping[str, float | None], max_concurrency: int
    ) -> None:
        self._min_intervals = {
            name: 1.0 / rate
            for name, rate in rate_limits.items()
            if rate is not None and rate > 0
        }
        self._slots = threading.Semaphore(max_concurrency)
        self._gates: dict[str, threading.Lock] = {}
        self._next_slot: dict[str, float] = {}

    def acquire(self, rate_class: str = "default") -> None:
        """Take one concurrency slot and wait for the class's next slot."""
        self._slots.acquire()
        interval = self._min_intervals.get(rate_class)
        if interval is None:
            return
        try:
            while True:
                gate = self._gates.setdefault(rate_class, threading.Lock())
                with gate:
                    wait = self._next_slot.get(rate_class, 0.0) - _now()
                    if wait <= 0:
                        self._next_slot[rate_class] = _now() + interval
                        return
                sleep(wait)
        except BaseException:
            self._slots.release()
            raise

    def release(self) -> None:
        """Give back the concurrency slot taken by :meth:`acquire`."""
        self._slots.release()


def maybe_await(value: Any) -> Any:
    """Return ``value`` unchanged; sync code has nothing to await."""
    return value


def run_bounded[T](
    fn: Callable[[T], Any],
    items: Sequence[T],
    concurrency: int,
) -> list[Any]:
    """Run ``fn`` over ``items`` on at most ``concurrency`` threads.

    Results keep the input order; the first failure re-raises.
    """
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        return list(executor.map(fn, items))
