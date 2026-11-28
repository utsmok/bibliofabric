"""Read ROR data dumps (zip archives from Zenodo) without loading them whole.

A dump zip holds one JSON file (a top-level array of organization records in
the API's own schema) and one CSV file with the same records.
:func:`iter_dump_records` streams the JSON member record by record, so a
dump of 150,000 records never sits in memory at once. Use
:func:`index_external_ids` to build lookup tables from the records you need.
"""

import json
import zipfile
from collections.abc import Iterable, Iterator
from io import TextIOBase, TextIOWrapper
from pathlib import Path

from bibliofabric import validate_model
from bibliofabric.exceptions import ConfigurationError

from .models import Organization

#: Characters read from the zip member per iteration.
_CHUNK_SIZE = 1 << 20

#: Whitespace and array punctuation skipped between two records.
_SEPARATORS = frozenset(" \t\r\n,[")


def iter_dump_records(zip_path: Path | str) -> Iterator[Organization]:
    """Yield every organization record of a downloaded dump zip.

    Args:
        zip_path: Path to a ``ror-data`` zip as downloaded from Zenodo.

    Raises:
        ConfigurationError: The zip has no ``.json`` member, or the member is
            not a JSON array, or it ends in the middle of a record.
    """
    with zipfile.ZipFile(zip_path) as archive:
        member = next(
            (name for name in archive.namelist() if name.endswith(".json")), None
        )
        if member is None:
            raise ConfigurationError(f"{zip_path} contains no .json member.")
        with archive.open(member) as raw:
            yield from _iter_json_array(TextIOWrapper(raw, encoding="utf-8"))


def index_external_ids(
    records: Iterable[Organization],
    id_type: str,
) -> dict[str, list[Organization]]:
    """Group records by every ``external_ids.all`` value of one ``id_type``.

    Keys are compacted (whitespace removed, lowercased), so an ISNI typed as
    ``0000000403998953`` finds the record that stores
    ``0000 0004 0399 8953``. Each key maps to the records carrying it, in
    dump order.
    """
    index: dict[str, list[Organization]] = {}
    for record in records:
        for value in record.external_ids_of_type(id_type):
            index.setdefault(_compact_id(value), []).append(record)
    return index


def compact_external_id(value: str) -> str:
    """Return ``value`` in the key form :func:`index_external_ids` uses."""
    return _compact_id(value)


def _iter_json_array(text: TextIOBase) -> Iterator[Organization]:
    """Yield the elements of a top-level JSON array read from ``text``."""
    decoder = json.JSONDecoder()
    buffer = ""
    opened = False
    while True:
        chunk = text.read(_CHUNK_SIZE)
        buffer += chunk
        position = 0
        while True:
            length = len(buffer)
            while position < length and buffer[position] in _SEPARATORS:
                opened = opened or buffer[position] == "["
                position += 1
            if position >= length:
                break
            if not opened:
                raise ConfigurationError("Dump member is not a JSON array.")
            if buffer[position] == "]":
                return
            try:
                record, end = decoder.raw_decode(buffer, position)
            except json.JSONDecodeError as error:
                if chunk:
                    break  # the record continues in the next chunk
                raise ConfigurationError(
                    f"Dump member is truncated or invalid JSON: {error}"
                ) from error
            yield validate_model(Organization, record)
            position = end
        buffer = buffer[position:]
        if not chunk:
            if not opened:
                raise ConfigurationError("Dump member is not a JSON array.")
            return


def _compact_id(value: str) -> str:
    return "".join(value.split()).lower()


__all__ = [
    "compact_external_id",
    "index_external_ids",
    "iter_dump_records",
]
