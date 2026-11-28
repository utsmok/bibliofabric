# Changelog

All notable changes to opcitato are documented here. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial client for the OpenCitations Index API v2: `IndexClient` with
  `citations()`, `references()`, `citation()`, `citation_count()`,
  `reference_count()`, and `venue_citation_count()`.
- Initial client for the OpenCitations Meta API v1: `MetaClient` with
  `metadata()`, `author()`, and `editor()`; `metadata()` packs several
  identifiers into one request with the `__` separator.
- The SPARQL endpoints of both datasets: `sparql()` returns the SPARQL 1.1
  JSON answer as a `SparqlResult`, and `sparql_text()` returns the XML,
  CSV, TSV, Turtle, or N-Triples representation as text. Both accept
  `method="POST"` for long queries.
- Pydantic models `SparqlResult`, `SparqlResults`, `SparqlHead`, and
  `SparqlTerm` for the SPARQL answers.
- Row-shaping parameters on every row operation: `require`, `filter`,
  `sort`, and `format` (`json` or `csv`, parsed into the same models).
- Pydantic models `Citation`, `Count`, and `MetadataRecord`, plus
  `ParsedIdentifier` and `parse_identifiers()` for the space-separated
  identifier strings the APIs return.
- Generated sync twin: `OpcitatoSyncClient`, `IndexSyncClient`,
  `MetaSyncClient`.

### Fixed

- Identifiers are percent-encoded before they enter the URL path. A DOI
  with `#` or `?` used to lose everything after that character.
- A JSON body that is not a list raises `ConfigurationError` instead of
  surfacing as an index error.
- A count route that answers a zero row returns `0`.
