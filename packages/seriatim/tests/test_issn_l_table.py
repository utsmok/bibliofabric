"""Readers for the ISSN-L table zip, against lines copied from the 2026-11-27 export."""

import zipfile

import pytest
from seriatim import (
    ConfigurationError,
    IssnLink,
    iter_issn_l_clusters,
    iter_issn_to_issn_l,
)

TO_ISSN_L = (
    "ISSN\tISSN-L\n"
    "0000-0019\t0000-0019\tta\n"
    "2150-4008\t0000-0019\tcr\n"
    "0000-0027\t0000-0027\n"
)
TO_ISSN = "ISSN-L\tISSN\n0000-0019\t2150-4008\t0000-0019\n0000-0027\t0000-0027\n"


def make_zip(path, members):
    with zipfile.ZipFile(path, "w") as archive:
        for name, text in members.items():
            archive.writestr(name, text)
    return path


@pytest.fixture
def table(tmp_path):
    return make_zip(
        tmp_path / "issnltables.zip",
        {
            "ISSN_ISSN-L_table.20261127.txt": "readme",
            "20261127.ISSN-to-ISSN-L.txt": TO_ISSN_L,
            "20261127.ISSN-L-to-ISSN.txt": TO_ISSN,
        },
    )


def test_issn_to_issn_l_rows_carry_the_medium_code(table):
    assert list(iter_issn_to_issn_l(table)) == [
        IssnLink("0000-0019", "0000-0019", "ta"),
        IssnLink("2150-4008", "0000-0019", "cr"),
        IssnLink("0000-0027", "0000-0027", None),
    ]


def test_issn_l_clusters_list_every_linked_issn(table):
    assert list(iter_issn_l_clusters(table)) == [
        ("0000-0019", ["2150-4008", "0000-0019"]),
        ("0000-0027", ["0000-0027"]),
    ]


def test_missing_member_raises(tmp_path):
    archive = make_zip(tmp_path / "empty.zip", {"readme.txt": "x"})
    with pytest.raises(ConfigurationError, match="ISSN-to-ISSN-L"):
        list(iter_issn_to_issn_l(archive))
