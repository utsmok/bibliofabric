"""Reading dump archives without loading them whole (pure functions, both variants)."""

import json
import zipfile

import pytest
import rorifer.dump as dump_module
from rorifer import (
    ConfigurationError,
    Organization,
    index_external_ids,
    iter_dump_records,
)

from .conftest import load_fixture, organization

MEMBER = "v2.16-2026-11-19-ror-data.json"
WEIRD_NAME = 'Weird "name" {with} [brackets], commas'


def write_dump(path, payload: bytes, *, member: str = MEMBER) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(member, payload)
        archive.writestr("v2.16-2026-11-19-ror-data.csv", "id,status\n")


def test_iter_dump_records_yields_every_record(tmp_path):
    records = [
        organization("006hf6230"),
        load_fixture("organization_funder.json"),
        organization("001z21q04", status="inactive"),
    ]
    write_dump(tmp_path / "ror.zip", json.dumps(records).encode())

    loaded = list(iter_dump_records(tmp_path / "ror.zip"))

    assert [record.id for record in loaded] == [record["id"] for record in records]
    assert loaded[1].display_name == "U.S. National Science Foundation"
    assert loaded[2].status == "inactive"


def test_iter_dump_records_crosses_chunk_boundaries(tmp_path, monkeypatch):
    """Records split across read chunks still decode, including braces in strings."""
    monkeypatch.setattr(dump_module, "_CHUNK_SIZE", 256)
    records = [
        organization(
            f"{index:08x}",
            names=[{"lang": None, "types": ["alias"], "value": WEIRD_NAME}],
        )
        for index in range(1500)
    ]
    write_dump(tmp_path / "ror.zip", json.dumps(records).encode())

    loaded = list(iter_dump_records(tmp_path / "ror.zip"))

    assert len(loaded) == 1500
    assert loaded[-1].names[0].value == WEIRD_NAME


def test_iter_dump_records_reads_indented_array_layout(tmp_path):
    records = [organization(f"{index:08x}") for index in range(50)]
    write_dump(tmp_path / "ror.zip", json.dumps(records, indent=4).encode())
    assert len(list(iter_dump_records(tmp_path / "ror.zip"))) == 50


def test_iter_dump_records_requires_a_json_member(tmp_path):
    with zipfile.ZipFile(tmp_path / "ror.zip", "w") as archive:
        archive.writestr("ror-data.csv", "id\n")
    with pytest.raises(ConfigurationError, match="no .json member"):
        list(iter_dump_records(tmp_path / "ror.zip"))


def test_iter_dump_records_rejects_non_array_member(tmp_path):
    write_dump(tmp_path / "ror.zip", b'{"id": "https://ror.org/006hf6230"}')
    with pytest.raises(ConfigurationError, match="not a JSON array"):
        list(iter_dump_records(tmp_path / "ror.zip"))


def test_iter_dump_records_reports_truncated_member(tmp_path):
    write_dump(
        tmp_path / "ror.zip", b'[{"id": "https://ror.org/006hf6230"}, {"id": "https'
    )
    with pytest.raises(ConfigurationError, match="truncated or invalid JSON"):
        list(iter_dump_records(tmp_path / "ror.zip"))


def test_index_external_ids_compacts_keys():
    utwente = load_fixture("organization.json")
    nsf = load_fixture("organization_funder.json")
    records = [
        Organization.model_validate(
            organization("006hf6230", external_ids=utwente["external_ids"])
        ),
        Organization.model_validate(
            organization("021nxhr62", external_ids=nsf["external_ids"])
        ),
    ]

    index = index_external_ids(records, "fundref")

    assert set(index) == {
        "501100001834",
        "501100007661",
        "501100009404",
        "501100015450",
        "100000001",
        "100015388",
        "100023581",
    }
    assert index["501100001834"][0].id == "https://ror.org/006hf6230"
    assert index_external_ids([], "grid") == {}


def test_index_external_ids_ignores_other_schemes_and_compacts():
    record = Organization.model_validate(
        organization(
            "006hf6230",
            external_ids=[
                {"type": "wikidata", "all": ["Q1547084"]},
                {"type": "isni", "all": ["0000 0004 0399 8953"]},
            ],
        )
    )
    assert list(index_external_ids([record], "isni")) == ["0000000403998953"]
    assert index_external_ids([record], "fundref") == {}
