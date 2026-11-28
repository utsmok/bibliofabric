"""Parser for the server-rendered search result page of the Portal.

The Portal search answers HTML only, so this module reads the result rows
with :mod:`html.parser` and maps them onto typed models. The markup this
parses is real server output (fixture ``search_results.html``, trimmed,
2026-11-27); if the Portal changes it, :func:`parse_search_page` raises
:class:`bibliofabric.exceptions.APIError` instead of returning guesses.
"""

from html.parser import HTMLParser

from bibliofabric.exceptions import APIError

from .models import OtherMedium, SearchHit, SearchPage

_HITS_CLASS = "search-results__hits-items"
_RECORD_CLASS = "search-results__record"

#: Text of the field label that precedes the sibling medium links.
_OTHER_MEDIUM_LABEL = "other medium"


def _has_class(attrs: list[tuple[str, str | None]], token: str) -> bool:
    """Return ``True`` when the ``class`` attribute contains ``token``."""
    for name, value in attrs:
        if name == "class" and value and token in value.split():
            return True
    return False


def _attr(attrs: list[tuple[str, str | None]], name: str) -> str | None:
    """Return the value of one attribute, or ``None``."""
    for key, value in attrs:
        if key == name:
            return value
    return None


def _excerpt(html: str) -> str:
    """Return a short body excerpt for error reporting."""
    return " ".join(html[:400].split())


class _SearchPageParser(HTMLParser):
    """Streaming parser for the ``search-results__hits-items`` container."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.total: int | None = None
        self.hits: list[SearchHit] = []
        self._hit: SearchHit | None = None
        self._label: str | None = None
        self._capture: tuple[str, str] | None = None
        self._buffer: list[str] = []
        self._other_href: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "div":
            self._open_hits(attrs)
            return
        if tag == "article":
            self._open_record(attrs)
            return
        hit = self._hit
        if hit is None:
            return
        if tag == "dd":
            self._open_field(attrs)
            return
        if tag == "span":
            self._open_badge(attrs)
            return
        if tag == "a":
            self._open_link(attrs)
            return
        if tag == "h2":
            self._open_title(attrs)
            return
        if tag == "dt":
            self._start_capture(tag, "label")

    def handle_data(self, data: str) -> None:
        if self._capture is not None:
            self._buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._capture is not None and self._capture[0] == tag:
            self._flush()
        if tag == "article" and self._hit is not None:
            self.hits.append(self._hit)
            self._hit = None
            self._label = None

    # --- element handlers -------------------------------------------------

    def _open_hits(self, attrs: list[tuple[str, str | None]]) -> None:
        """Read the ``data-hits`` total of the hits container."""
        if not _has_class(attrs, _HITS_CLASS):
            return
        raw_total = _attr(attrs, "data-hits")
        if raw_total is not None and raw_total.isdigit():
            self.total = int(raw_total)

    def _open_record(self, attrs: list[tuple[str, str | None]]) -> None:
        """Start one hit when a record row opens."""
        if _has_class(attrs, _RECORD_CLASS):
            self._hit = SearchHit()

    def _open_field(self, attrs: list[tuple[str, str | None]]) -> None:
        """Read the identifier cell and start label captures."""
        code = _attr(attrs, "data-issn")
        if code:
            hit = self._hit
            if hit is not None:
                hit.issn = code
            return
        code = _attr(attrs, "data-medium")
        if code:
            hit = self._hit
            if hit is not None:
                hit.medium = code
            self._start_capture("dd", "medium_label")
            return
        code = _attr(attrs, "data-country")
        if code:
            hit = self._hit
            if hit is not None:
                hit.country = code
            self._start_capture("dd", "country_label")

    def _open_badge(self, attrs: list[tuple[str, str | None]]) -> None:
        """Read the record category badge and cancelled ISSN spans."""
        hit = self._hit
        if hit is None:
            return
        code = _attr(attrs, "data-category")
        if code:
            hit.category = code
            self._start_capture("span", "category_label")
            return
        code = _attr(attrs, "data-cancelled-issn")
        if code:
            hit.cancelled_issns.append(code)

    def _open_link(self, attrs: list[tuple[str, str | None]]) -> None:
        """Read cluster ids and the sibling medium or record links."""
        hit = self._hit
        if hit is None:
            return
        code = _attr(attrs, "data-issnl")
        if code:
            hit.issn_l = code
            return
        code = _attr(attrs, "data-issnh")
        if code:
            hit.issn_h = code
            return
        href = _attr(attrs, "href")
        if not href or not href.startswith("/resource/"):
            return
        if self._label == _OTHER_MEDIUM_LABEL:
            self._other_href = href
            self._start_capture("a", "other_label")
        elif hit.detail_path is None:
            hit.detail_path = href.split("?", 1)[0]

    def _open_title(self, attrs: list[tuple[str, str | None]]) -> None:
        """Read the key title of the row."""
        code = _attr(attrs, "data-key-title")
        hit = self._hit
        if code and hit is not None:
            hit.title = code

    # --- text capture -----------------------------------------------------

    def _start_capture(self, tag: str, sink: str) -> None:
        """Collect the text of one element into ``sink``."""
        self._capture = (tag, sink)
        self._buffer = []

    def _flush(self) -> None:
        """Store the collected text of the element that just closed."""
        capture = self._capture
        if capture is None:
            return
        sink = capture[1]
        text = " ".join("".join(self._buffer).split())
        self._capture = None
        self._buffer = []
        hit = self._hit
        if hit is None:
            return
        if sink == "label":
            self._label = text.rstrip(":").lower()
        elif sink == "medium_label":
            hit.medium_label = text
            self._label = None
        elif sink == "country_label":
            hit.country_label = text
            self._label = None
        elif sink == "category_label":
            hit.category_label = text
        elif sink == "other_label":
            if self._other_href and text:
                hit.other_media.append(OtherMedium(label=text, href=self._other_href))
            self._other_href = None
            self._label = None


def parse_search_page(html: str, *, page: int, page_size: int) -> SearchPage:
    """Parse one search result page into a typed :class:`SearchPage`.

    ``total`` is the ``data-hits`` value of the hits container and ``hits``
    are the record rows in display order. Raises
    :class:`bibliofabric.exceptions.APIError` when the page holds no hits
    container at all, which means the Portal markup changed.
    """
    parser = _SearchPageParser()
    parser.feed(html)
    parser.close()
    if parser.total is None and not parser.hits:
        raise APIError(
            "The search result page held no search-results__hits-items "
            "container; the Portal markup may have changed.",
            body=_excerpt(html),
        )
    return SearchPage(
        total=parser.total,
        page=page,
        page_size=page_size,
        hits=parser.hits,
    )


__all__ = ["parse_search_page"]
