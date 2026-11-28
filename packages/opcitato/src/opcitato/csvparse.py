"""Reader for the CSV representation of the OpenCitations APIs.

Every operation answers JSON by default and CSV with ``format=csv``; the
CSV header repeats the JSON field names, so rows parse into the same
Pydantic models.
"""

import csv
import io


def parse_csv_rows(text: str) -> list[dict[str, str]]:
    """Parse an OpenCitations CSV table into row dictionaries.

    Short rows are padded with empty strings, exactly like the JSON
    representation fills unknown fields with ``""``. A ``None`` key (a row
    longer than the header) is dropped, because no model field can receive
    it.
    """
    reader = csv.DictReader(io.StringIO(text))
    return [
        {
            key: value if value is not None else ""
            for key, value in row.items()
            if key is not None
        }
        for row in reader
    ]


__all__ = ["parse_csv_rows"]
