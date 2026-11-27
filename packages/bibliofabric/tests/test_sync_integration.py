"""The generated sync client works inside a running event loop and threads."""

import asyncio
import threading

import pytest
from bibliofabric import BaseApiSettings, SyncBaseApiClient
from bibliofabric._sync import _concurrency


class _Unwrapper:
    """Unwraps a flat JSON body; enough for the raw client calls below."""

    def results(self, body: dict) -> list[dict]:
        return body.get("results", [])

    def item(self, body: dict) -> dict:
        return body

    def total(self, body: dict) -> int | None:
        return body.get("total")

    def next_cursor(self, body: dict) -> str | None:
        return None

    def meta(self, body: dict) -> dict:
        return {}


def make_sync_client() -> SyncBaseApiClient:
    return SyncBaseApiClient(
        base_url="https://loop.test/api",
        settings=BaseApiSettings(),
        unwrapper=_Unwrapper(),
    )


def test_sync_client_inside_running_event_loop(httpx_mock):
    httpx_mock.add_response(url="https://loop.test/api/ping", json={"ok": True})

    async def call_from_coroutine() -> object:
        client = make_sync_client()
        try:
            # A blocking sync call inside a coroutine: the sync path never
            # starts or touches the running loop, so this must just work.
            return client.get_json("ping")
        finally:
            client.close()

    assert asyncio.run(call_from_coroutine()) == {"ok": True}


def test_sync_client_from_threads(httpx_mock):
    httpx_mock.add_response(
        url="https://loop.test/api/ping", json={"ok": True}, is_reusable=True
    )
    results: list[object] = []
    errors: list[Exception] = []

    def worker() -> None:
        client = make_sync_client()
        try:
            results.append(client.get_json("ping"))
        except Exception as error:  # noqa: BLE001 - reported below
            errors.append(error)
        finally:
            client.close()

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    assert results == [{"ok": True}] * 4


def test_sync_maybe_await_rejects_coroutine():
    async def async_cb() -> None:
        return None

    with pytest.raises(TypeError, match="synchronous function"):
        _concurrency.maybe_await(async_cb())
