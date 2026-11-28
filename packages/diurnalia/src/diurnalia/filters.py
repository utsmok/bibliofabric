"""Query builders for the DOAJ search routes.

DOAJ carries the search query in the path and reads an Elasticsearch query
string. The helpers build the fielded clauses for the two identifier
lookups the package wraps. Field names use the DOAJ short forms (`issn`,
`doi`, `title`, `publisher`, `license`, `abstract`); the `.exact` suffix
matches the stored spelling on any other string field.
"""

from bibliofabric.exceptions import ConfigurationError
from bibliofabric.ids import normalize_doi, normalize_issn


def issn_query(issn: str) -> str:
    """Return the `issn:` clause for a journal ISSN.

    Accepts the grouped (``1932-6203``) and the compact (``19326203``)
    spelling and an ISSN URL. The clause matches the print and the
    electronic ISSN of a journal, because DOAJ indexes both in one field.
    """
    normalized = normalize_issn(issn)
    if not normalized:
        raise ConfigurationError(f"not a recognizable ISSN: {issn!r}")
    return f"issn:{normalized}"


def doi_query(doi: str) -> str:
    """Return the `doi:` clause for an article DOI.

    Accepts a bare DOI (``10.3389/fpubh.2020.00115``) and a DOI URL. DOAJ
    escapes the forward slash of a DOI itself, so the clause can carry the
    plain DOI.
    """
    normalized = normalize_doi(doi)
    if not normalized:
        raise ConfigurationError(f"not a recognizable DOI: {doi!r}")
    return f"doi:{normalized}"


__all__ = ["doi_query", "issn_query"]
