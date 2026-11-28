"""Reader for the public DOAJ journal CSV export (``https://doaj.org/csv``)."""

import csv
from collections.abc import Iterator
from pathlib import Path


def iter_journal_csv(path: Path | str) -> Iterator[dict[str, str]]:
    """Yield one dict per journal row of a downloaded DOAJ journal CSV.

    The keys are the column headers of the export as DOAJ writes them, for
    example ``"Journal title"``, ``"Journal ISSN (print version)"``, and
    ``"Journal EISSN (online version)"``. Every value is a string; an empty
    cell is ``""``. The file is read row by row, so memory use stays flat.
    """
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle)


__all__ = ["iter_journal_csv"]
