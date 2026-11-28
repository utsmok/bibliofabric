"""Crosswalk helpers between Crossref Funder Registry DOIs and ROR FundRef ids.

ROR stores Crossref Funder Registry identifiers as ``fundref`` external ids
(the DOI suffix, for example ``100000001``). Crossref exposes the same
registry as DOIs under the ``10.13039/`` prefix (``10.13039/100000001``).
"""

import re

from bibliofabric.ids import normalize_doi

#: DOI prefix of the Crossref Funder Registry (now maintained inside ROR).
FUNDREF_DOI_PREFIX = "10.13039/"

#: FundRef ids are 6 to 12 digits (``100006`, `100000001`, `501100001834`).
_FUNDREF_ID_PATTERN = re.compile(r"^\d{6,12}$")


def fundref_id_from_doi(doi: str) -> str:
    """Return the FundRef id of a Crossref funder DOI.

    ``10.13039/100000001`` (also as a ``https://doi.org/...`` URL) becomes
    ``100000001``. A DOI with another prefix raises ``ValueError``.
    """
    normalized = normalize_doi(doi)
    fundref_id = (
        normalized.removeprefix(FUNDREF_DOI_PREFIX)
        if normalized.startswith(FUNDREF_DOI_PREFIX)
        else ""
    )
    if not _FUNDREF_ID_PATTERN.match(fundref_id):
        raise ValueError(f"Not a Crossref Funder Registry DOI: {doi!r}")
    return fundref_id


def fundref_doi_from_id(fundref_id: str) -> str:
    """Return the Crossref funder DOI of a FundRef id (``100000001`` to ``10.13039/100000001``)."""
    fundref_id = fundref_id.strip()
    if not _FUNDREF_ID_PATTERN.match(fundref_id):
        raise ValueError(f"Not a FundRef id: {fundref_id!r}")
    return f"{FUNDREF_DOI_PREFIX}{fundref_id}"


__all__ = ["FUNDREF_DOI_PREFIX", "fundref_doi_from_id", "fundref_id_from_doi"]
