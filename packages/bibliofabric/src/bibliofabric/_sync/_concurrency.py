"""Sync twins of ``bibliofabric._async._concurrency``.

Hand-written and excluded from generation, like its async counterpart. This
module never touches an event loop: plain ``time.sleep``, ``threading``
locks, and a thread pool for bounded batch calls.
"""

import inspect
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
    minimum-interval gate per class, booked in O(1) on a shared monotonic
    timeline, and one shared concurrency bound claimed after waiting so
    waiting callers of one class never starve another class's concurrency
    slots. Undeclared rate classes fall back to ``"default"``.
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
        self._slots = threading.Semaphore(max_concurrency)
        self._gates: dict[str, threading.Lock] = {
            name: threading.Lock()
            for name, interval in self._intervals.items()
            if interval is not None
        }
        self._next_slot: dict[str, float] = {}

    def acquire(self, rate_class: str = "default") -> None:
        """Wait for the class's next pacing slot, then claim a concurrency slot."""
        if rate_class in self._intervals:
            effective_class = rate_class
            interval = self._intervals[rate_class]
        else:
            effective_class = "default"
            interval = self._intervals.get("default")

        if interval is not None:
            gate = self._gates[effective_class]
            with gate:
                now = _now()
                slot = max(now, self._next_slot.get(effective_class, float("-inf")))
                self._next_slot[effective_class] = slot + interval
            wait = slot - now
            if wait > 0:
                sleep(wait)

        self._slots.acquire()

    def release(self) -> None:
        """Give back the concurrency slot taken by :meth:`acquire`."""
        self._slots.release()


def maybe_await(value: Any) -> Any:
    """Return ``value`` unchanged; raise ``TypeError`` if given an awaitable."""
    if inspect.isawaitable(value):
        if inspect.iscoroutine(value):
            value.close()
        raise TypeError(
            "Sync clients cannot await an async callback; pass a synchronous function."
        )
    return value


def run_bounded[T, R](
    fn: Callable[[T], R],
    items: Sequence[T],
    concurrency: int,
) -> list[R]:
    """Run ``fn`` over ``items`` on at most ``concurrency`` threads.

    Results keep the input order; the first failure cancels queued futures and
    re-raises.
    """
    if concurrency <= 0:
        raise ValueError(f"concurrency must be positive, got {concurrency}.")
    if not items:
        return []
    executor = ThreadPoolExecutor(max_workers=min(concurrency, len(items)))
    futures = [executor.submit(fn, item) for item in items]
    failed = False
    try:
        return [future.result() for future in futures]
    except BaseException:
        failed = True
        raise
    finally:
        executor.shutdown(wait=True, cancel_futures=failed)
