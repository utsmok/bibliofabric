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
- Row-shaping parameters on every row operation: `require`, `filter`,
  `sort`, and `format` (`json` or `csv`, parsed into the same models).
- Pydantic models `Citation`, `Count`, and `MetadataRecord`, plus
  `ParsedIdentifier` and `parse_identifiers()` for the space-separated
  identifier strings the APIs return.
- Generated sync twin: `OpcitatoSyncClient`, `IndexSyncClient`,
  `MetaSyncClient`.
