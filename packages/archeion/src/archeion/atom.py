"""Parse the Atom 1.0 feeds of the arXiv query API into plain dicts.

The API answers every query with one Atom feed: OpenSearch elements carry
the paging totals, and each ``entry`` is one paper version. The parser turns
the feed into the dict shape that :class:`archeion.ArcheionUnwrapper` reads
and the entry dicts into the shape that :class:`archeion.ArxivEntry`
validates, so the models never see XML.
"""

from typing import Any
from xml.etree.ElementTree import Element, ParseError, fromstring

from bibliofabric.exceptions import ConfigurationError

ATOM = "{http://www.w3.org/2005/Atom}"
OPENSEARCH = "{http://a9.com/-/spec/opensearch/1.1/}"
ARXIV = "{http://arxiv.org/schemas/atom}"

#: Entries whose ``id`` starts with this URL report a query error.
ERROR_ID_PREFIX = "https://arxiv.org/api/errors"


def parse_feed(text: str) -> dict[str, Any]:
    """Return the feed as ``{"id", "updated", "total", "start", "per_page",
    "entries"}``.

    Raises :class:`ConfigurationError` when the feed is an error feed (an
    entry whose ``id`` points at ``https://arxiv.org/api/errors``), because
    the API answers that for malformed ids and queries.
    """
    try:
        root = fromstring(text)
    except ParseError as error:
        raise ConfigurationError(
            f"arXiv answered a body that is not XML: {error}"
        ) from error
    entries = [_entry(node) for node in root.findall(f"{ATOM}entry")]
    for entry in entries:
        if str(entry.get("id") or "").startswith(ERROR_ID_PREFIX):
            raise ConfigurationError(
                f"arXiv rejected the query: {entry.get('summary')}"
            )
    return {
        "id": _text(root, f"{ATOM}id"),
        "updated": _text(root, f"{ATOM}updated"),
        "total": _int(root, f"{OPENSEARCH}totalResults"),
        "start": _int(root, f"{OPENSEARCH}startIndex"),
        "per_page": _int(root, f"{OPENSEARCH}itemsPerPage"),
        "entries": entries,
    }


def _entry(node: Element) -> dict[str, Any]:
    """Return one ``entry`` element as a dict."""
    primary = node.find(f"{ARXIV}primary_category")
    return {
        "id": _text(node, f"{ATOM}id"),
        "title": _squash(_text(node, f"{ATOM}title")),
        "summary": _strip(_text(node, f"{ATOM}summary")),
        "published": _text(node, f"{ATOM}published"),
        "updated": _text(node, f"{ATOM}updated"),
        "authors": [
            {
                "name": _text(author, f"{ATOM}name"),
                "affiliations": [
                    text
                    for text in (
                        _strip(element.text)
                        for element in author.findall(f"{ARXIV}affiliation")
                    )
                    if text
                ],
            }
            for author in node.findall(f"{ATOM}author")
        ],
        "links": [dict(link.attrib) for link in node.findall(f"{ATOM}link")],
        "categories": [
            category.attrib["term"]
            for category in node.findall(f"{ATOM}category")
            if "term" in category.attrib
        ],
        "primary_category": primary.attrib.get("term") if primary is not None else None,
        "comment": _strip(_text(node, f"{ARXIV}comment")),
        "journal_ref": _strip(_text(node, f"{ARXIV}journal_ref")),
        "doi": _strip(_text(node, f"{ARXIV}doi")),
    }


def _text(node: Element, tag: str) -> str | None:
    element = node.find(tag)
    return element.text if element is not None else None


def _int(node: Element, tag: str) -> int | None:
    value = _text(node, tag)
    return int(value) if value is not None and value.strip().isdigit() else None


def _strip(value: str | None) -> str | None:
    return value.strip() if value is not None else None


def _squash(value: str | None) -> str | None:
    """Collapse the line breaks and indentation that arXiv keeps in titles."""
    return " ".join(value.split()) if value is not None else None


__all__ = ["ERROR_ID_PREFIX", "parse_feed"]
