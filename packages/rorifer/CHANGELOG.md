# Changelog

All notable changes to rorifer are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial client for the ROR API v2: `RoriferClient` with the
  `organizations` resource (`get`, `exists`, `search`, `iterate`, `count`,
  `match_affiliation`, `find_by_external_id`, `find_by_funder_doi`) and the
  `dumps` helper for the Zenodo data dumps (`list`, `latest`, `download`).
- Generated sync twin: `RoriferSyncClient`, `OrganizationsSyncClient`,
  `DumpsSyncClient`.
- Pydantic models for organizations, affiliation matches, and dumps.
- `iter_dump_records()` and `index_external_ids()` to read a downloaded dump
  without loading it whole.
- `fundref_id_from_doi()` and `fundref_doi_from_id()` for the Crossref Funder
  Registry crosswalk.
