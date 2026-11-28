"""bibliofabric ``ResponseUnwrapper`` for the bioRxiv API envelopes.

Every answer carries ``messages`` (a list with one object, or one object on
the statistics routes) and the records under ``collection``, or under
``"bioRxiv content statistics"`` / ``"medRxiv content statistics"`` on the
statistics routes. ``messages[0].status`` is ``ok``, a ``no ... found``
text for an empty answer, or an error text such as ``Both dates must be in
yyyy-mm-dd format`` (the API still answers HTTP 200).
"""

from typing import Any

from bibliofabric.exceptions import ConfigurationError

_STATISTICS_SUFFIX = "content statistics"


def message(body: Any) -> dict[str, Any]:
    """Return the first ``messages`` object, or an empty dict."""
    messages = body.get("messages") if isinstance(body, dict) else None
    if isinstance(messages, list) and messages and isinstance(messages[0], dict):
        return messages[0]
    return messages if isinstance(messages, dict) else {}


def check_status(body: Any) -> None:
    """Raise :class:`ConfigurationError` for an error status in ``messages``.

    ``ok`` and the ``no posts found`` / ``no articles found`` family pass;
    every other status names a request the API rejected.
    """
    status = str(message(body).get("status") or "").strip()
    if status == "ok" or status.lower().startswith("no "):
        return
    raise ConfigurationError(f"The bioRxiv API rejected the request: {status!r}.")


class ProdromusUnwrapper:
    """Extracts records, totals, and metadata from bioRxiv envelopes."""

    def results(self, body: Any) -> list[dict[str, Any]]:
        """Return the records of ``collection`` or of the statistics key."""
        if not isinstance(body, dict):
            return []
        records = body.get("collection")
        if records is None:
            records = next(
                (
                    value
                    for key, value in body.items()
                    if key.endswith(_STATISTICS_SUFFIX)
                ),
                None,
            )
        if not isinstance(records, list):
            return []
        return [record for record in records if isinstance(record, dict)]

    def item(self, body: Any) -> dict[str, Any]:
        """Return the first record, or an empty dict."""
        records = self.results(body)
        return records[0] if records else {}

    def total(self, body: Any) -> int | None:
        """Return ``messages[0].total`` (sent as a string or a number)."""
        return _as_int(message(body).get("total"))

    def next_cursor(self, body: Any) -> str | None:
        """Return ``cursor + count`` while records remain, else ``None``.

        The API sends ``cursor`` as a number on the first page and as a
        string on later pages, so both forms count.
        """
        info = message(body)
        total = self.total(body)
        cursor, count = _as_int(info.get("cursor")), _as_int(info.get("count"))
        if cursor is None or not count:
            return None
        following = cursor + count
        return str(following) if total is not None and following < total else None

    def meta(self, body: Any) -> dict[str, Any]:
        """Return the ``messages`` object."""
        return dict(message(body))


def _as_int(value: Any) -> int | None:
    """Return ``value`` as an int when it is one or a string of digits."""
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return int(value) if isinstance(value, str) and value.isdigit() else None


__all__ = ["ProdromusUnwrapper", "check_status", "message"]
