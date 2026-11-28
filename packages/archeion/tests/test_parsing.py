"""Atom parsing and the entry model, against real feeds of 2026-11-28."""

import pytest
from archeion import ArxivEntry, ConfigurationError, parse_feed

from .conftest import load_fixture


def test_feed_totals_and_entry_fields():
    body = parse_feed(load_fixture("two_entries.xml"))
    assert body["total"] == 2
    assert body["start"] == 0
    assert body["per_page"] == 2
    entries = {entry["id"]: entry for entry in body["entries"]}
    maldacena = ArxivEntry.model_validate(
        entries["http://arxiv.org/abs/hep-th/9711200v3"]
    )
    assert maldacena.arxiv_id == "hep-th/9711200"
    assert maldacena.version == 3
    assert maldacena.doi == "10.1023/A:1026654312961"
    assert maldacena.journal_ref == "Adv.Theor.Math.Phys.2:231-252,1998"
    assert maldacena.primary_category == "hep-th"
    assert maldacena.pdf_url == "https://arxiv.org/pdf/hep-th/9711200v3"
    assert maldacena.author_names == ["Juan M. Maldacena"]
    attention = ArxivEntry.model_validate(entries["http://arxiv.org/abs/1706.03762v7"])
    assert attention.title == "Attention Is All You Need"
    assert attention.primary_category == "cs.CL"
    assert "cs.LG" in attention.categories
    assert attention.comment == "15 pages, 5 figures"


def test_title_whitespace_is_collapsed():
    body = parse_feed(
        load_fixture("empty.xml").replace(
            "</feed>",
            "<entry><id>http://arxiv.org/abs/1v1</id>"
            "<title>Line one\n   line two</title></entry></feed>",
        )
    )
    assert body["entries"][0]["title"] == "Line one line two"


def test_empty_feed_has_no_entries():
    body = parse_feed(load_fixture("empty.xml"))
    assert body["total"] == 0
    assert body["entries"] == []


def test_error_feed_raises():
    with pytest.raises(ConfigurationError, match="incorrect id format"):
        parse_feed(load_fixture("error_bad_id.xml"))


def test_non_xml_body_raises():
    with pytest.raises(ConfigurationError, match="not XML"):
        parse_feed("<html>")
