"""Readers for the public ISSN-L table (``/public/issnltables.zip``).

The zip holds a readme and two tab-separated files with a header row:

- ``<date>.ISSN-to-ISSN-L.txt``: one line per ISSN with its ISSN-L and a
  third column the readme does not mention. Its values (``ta``, ``cr``,
  ``co``, ``vd``, ...) are the medium codes of MARC 21 field 007, positions
  00 and 01: ``ta`` is printed text and ``cr`` an online resource.
- ``<date>.ISSN-L-to-ISSN.txt``: one line per ISSN-L followed by every ISSN
  that links to it, the ISSN-L itself included.

The readers open the zip and stream one file line by line, so memory use
stays flat for the 2.6 million lines of the 2026-11-28 table.
"""

import io
import zipfile
from collections.abc import Iterator
from pathlib import Path
from typing import NamedTuple

from bibliofabric.exceptions import ConfigurationError

#: Index of the medium code column in the ISSN-to-ISSN-L file.
_MEDIUM_COLUMN = 2


class IssnLink(NamedTuple):
    """One line of the ISSN-to-ISSN-L file."""

    issn: str
    issn_l: str
    medium: str | None


def iter_issn_to_issn_l(zip_path: Path | str) -> Iterator[IssnLink]:
    """Yield one :class:`IssnLink` per assigned ISSN, sorted by ISSN."""
    for fields in _rows(zip_path, ".ISSN-to-ISSN-L.txt"):
        medium = fields[_MEDIUM_COLUMN] if len(fields) > _MEDIUM_COLUMN else None
        yield IssnLink(issn=fields[0], issn_l=fields[1], medium=medium or None)


def iter_issn_l_clusters(zip_path: Path | str) -> Iterator[tuple[str, list[str]]]:
    """Yield ``(issn_l, issns)`` per ISSN-L, sorted by ISSN-L.

    ``issns`` lists every ISSN that links to the ISSN-L, in file order, and
    includes the ISSN-L itself.
    """
    for fields in _rows(zip_path, ".ISSN-L-to-ISSN.txt"):
        yield fields[0], [value for value in fields[1:] if value]


def _rows(zip_path: Path | str, suffix: str) -> Iterator[list[str]]:
    """Yield the tab-separated fields of each data line of one zip member."""
    with zipfile.ZipFile(zip_path) as archive:
        names = [name for name in archive.namelist() if name.endswith(suffix)]
        if len(names) != 1:
            raise ConfigurationError(
                f"Expected one '*{suffix}' file in {zip_path}, found {names}."
            )
        with archive.open(names[0]) as raw:
            lines = io.TextIOWrapper(raw, encoding="utf-8", newline="")
            next(lines, None)  # header row
            for line in lines:
                stripped = line.rstrip("\r\n")
                if stripped:
                    yield stripped.split("\t")


__all__ = ["IssnLink", "iter_issn_l_clusters", "iter_issn_to_issn_l"]
