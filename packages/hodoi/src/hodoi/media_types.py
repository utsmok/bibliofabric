"""Catalog of the media types answered by DOI content negotiation.

Use the constants instead of the raw strings. Which registration agency
answers which type is recorded in :data:`AGENCY_SUPPORT` and in
``docs/hodoi/upstream-quirks.md``; unsupported combinations answer HTTP 406.
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

#: Agency availability per the DOI Foundation content negotiation page
#: (https://citation.doi.org/docs.html), confirmed live on 2026-11-27.
AGENCY_SUPPORT: dict[str, tuple[str, ...]] = {
    CSL_JSON: ("Crossref", "DataCite", "mEDRA"),
    BIBTEX: ("Crossref", "DataCite", "mEDRA"),
    RIS: ("Crossref", "DataCite"),
    BIBLIOGRAPHY: ("Crossref", "DataCite", "mEDRA"),
    SCHEMAORG_JSONLD: ("DataCite",),
    UNIXREF_XML: ("Crossref",),
    UNIXSD_XML: ("Crossref",),
    DATACITE_XML: ("DataCite",),
    ONIX_DOI_XML: ("mEDRA",),
    RDF_XML: ("Crossref", "DataCite", "mEDRA"),
    TURTLE: ("Crossref", "DataCite", "mEDRA"),
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
