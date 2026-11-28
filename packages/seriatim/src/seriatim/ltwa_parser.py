"""Parser for the Title Word Abbreviation table of the Portal.

The LTWA page renders its rows as a server-rendered HTML table; this module
reads them with :mod:`html.parser` into typed entries. A page_size above
100 makes the Portal answer a page with an error alert and no table, which
parses as an empty list (verified 2026-11-27).
"""

from html.parser import HTMLParser

from .models import LtwaEntry

_ROW_CLASS = "ltwa-results__table-row"
_CELL_CLASS = "ltwa-results__cell"

#: The Portal renders an empty abbreviation cell as the literal text ``None``.
_NONE_TEXT = "None"


def _has_class(attrs: list[tuple[str, str | None]], token: str) -> bool:
    """Return ``True`` when the ``class`` attribute contains ``token``."""
    for name, value in attrs:
        if name == "class" and value and token in value.split():
            return True
    return False


class _LtwaParser(HTMLParser):
    """Streaming parser for ``ltwa-results__table`` rows."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.entries: list[LtwaEntry] = []
        self._cells: list[str | None] | None = None
        self._capture: bool = False
        self._buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr" and _has_class(attrs, _ROW_CLASS):
            self._cells = []
            return
        if tag == "td" and self._cells is not None and _has_class(attrs, _CELL_CLASS):
            self._capture = True
            self._buffer = []

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self._capture:
            text = " ".join("".join(self._buffer).split())
            cells = self._cells
            if cells is not None:
                cells.append(text or None)
            self._capture = False
            self._buffer = []
            return
        if tag == "tr" and self._cells is not None:
            cells = self._cells
            padded = list(cells) + [None] * (3 - len(cells))
            if cells:
                self.entries.append(
                    LtwaEntry(
                        word=padded[0] or "",
                        abbreviation=None if padded[1] == _NONE_TEXT else padded[1],
                        language=padded[2],
                    )
                )
            self._cells = None


def parse_ltwa_page(html: str) -> list[LtwaEntry]:
    """Parse one Title Word Abbreviation page into typed entries.

    Returns the rows in display order; a page with no table (the Portal
    error state) parses as an empty list.
    """
    parser = _LtwaParser()
    parser.feed(html)
    parser.close()
    return parser.entries


__all__ = ["parse_ltwa_page"]
