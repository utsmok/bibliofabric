# Changelog

All notable changes to hodoi are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial client for the DOI System proxy at doi.org: `HodoiClient` with
  `agencies()` (registration agency lookup, batched in chunks of 100),
  `handle()` (typed Handle.net records), `landing_url()`, `content()`
  (negotiated metadata with typed JSON models), and `raw()` (un-parsed bytes).
- Media type catalog in `hodoi.media_types` with the Crossref, DataCite,
  and mEDRA support matrix.
- Pydantic models for the `/ra/` answers, Handle records, and the CSL JSON,
  DataCite JSON, and schema.org JSON-LD representations.
- Generated sync twin: `HodoiSyncClient`.
