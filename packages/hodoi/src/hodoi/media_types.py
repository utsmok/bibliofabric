"""Catalog of the media types answered by DOI content negotiation.

Use the constants instead of the raw strings. Which registration agency
answers which type is recorded in :data:`AGENCY_SUPPORT` and in
``docs/hodoi/upstream-quirks.md``; unsupported combinations answer with an
HTTP error (406 in most cases).
"""

CSL_JSON = "application/vnd.citationstyles.csl+json"
DATACITE_JSON = "application/vnd.datacite.datacite+json"
DATACITE_XML = "application/vnd.datacite.datacite+xml"
SCHEMAORG_JSONLD = "application/vnd.schemaorg.ld+json"
UNIXREF_XML = "application/vnd.crossref.unixref+xml"
UNIXSD_XML = "application/vnd.crossref.unixsd+xml"
ONIX_DOI_XML = "application/vnd.medra.onixdoi+xml"
BIBTEX = "application/x-bibtex"
RIS = "application/x-research-info-systems"
BIBLIOGRAPHY = "text/x-bibliography"
RDF_XML = "application/rdf+xml"
TURTLE = "text/turtle"

#: JSON representations the client parses into models. Every other type is
#: returned as text (BibTeX, RIS, XML, formatted citations).
JSON_MEDIA_TYPES = (CSL_JSON, DATACITE_JSON, SCHEMAORG_JSONLD)

#: Agency availability, checked request by request against one DOI of each
#: agency on 2026-11-28 (Crossref 10.1038/nature12373, DataCite
#: 10.5281/zenodo.1238808, mEDRA 10.1400/56174). The DOI Foundation page
#: (https://citation.doi.org/docs.html) lists RIS as missing for mEDRA and
#: RDF XML and Turtle as served by DataCite; the live answers differ there.
AGENCY_SUPPORT: dict[str, tuple[str, ...]] = {
    CSL_JSON: ("Crossref", "DataCite", "mEDRA"),
    DATACITE_JSON: ("DataCite",),
    DATACITE_XML: ("DataCite",),
    SCHEMAORG_JSONLD: ("DataCite",),
    UNIXREF_XML: ("Crossref",),
    UNIXSD_XML: ("Crossref",),
    ONIX_DOI_XML: ("mEDRA",),
    BIBTEX: ("Crossref", "DataCite", "mEDRA"),
    RIS: ("Crossref", "DataCite", "mEDRA"),
    BIBLIOGRAPHY: ("Crossref", "DataCite", "mEDRA"),
    RDF_XML: ("Crossref", "mEDRA"),
    TURTLE: ("Crossref", "mEDRA"),
}

#: All catalogued media type strings, for iteration and tests.
MEDIA_TYPES: tuple[str, ...] = tuple(AGENCY_SUPPORT)

__all__ = [
    "AGENCY_SUPPORT",
    "BIBLIOGRAPHY",
    "BIBTEX",
    "CSL_JSON",
    "DATACITE_JSON",
    "DATACITE_XML",
    "JSON_MEDIA_TYPES",
    "MEDIA_TYPES",
    "ONIX_DOI_XML",
    "RDF_XML",
    "RIS",
    "SCHEMAORG_JSONLD",
    "TURTLE",
    "UNIXREF_XML",
    "UNIXSD_XML",
]
