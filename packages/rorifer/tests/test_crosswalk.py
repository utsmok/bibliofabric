"""Crosswalk helpers between Crossref Funder Registry DOIs and ROR FundRef ids."""

import pytest
from rorifer import fundref_doi_from_id, fundref_id_from_doi


@pytest.mark.parametrize(
    "doi",
    [
        "10.13039/100000001",
        "https://doi.org/10.13039/100000001",
        "10.13039/501100001834",
        "10.13039/100006",
    ],
)
def test_fundref_id_from_doi_strips_prefix(doi):
    suffix = doi.rsplit("/", 1)[-1]
    assert fundref_id_from_doi(doi) == suffix


@pytest.mark.parametrize("doi", ["10.1234/abc", "10.13039/abc", "100000001", ""])
def test_fundref_id_from_doi_rejects_other_dois(doi):
    with pytest.raises(ValueError, match="Not a Crossref Funder Registry DOI"):
        fundref_id_from_doi(doi)


def test_fundref_doi_from_id_adds_prefix():
    assert fundref_doi_from_id("100000001") == "10.13039/100000001"
    assert fundref_doi_from_id(" 501100001834 ") == "10.13039/501100001834"
    assert fundref_id_from_doi(fundref_doi_from_id("100006")) == "100006"


@pytest.mark.parametrize("fundref_id", ["abc", "12345", "100000012345678", ""])
def test_fundref_doi_from_id_rejects_malformed_ids(fundref_id):
    with pytest.raises(ValueError, match="Not a FundRef id"):
        fundref_doi_from_id(fundref_id)
