# Changelog

All notable changes to rorifer are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial client for the ROR API v2: `RoriferClient` with the
  `organizations` resource (`get`, `exists`, `search`, `iterate`, `collect`,
  `first`, `count`, `match_affiliation`, `find_by_external_id`,
  `find_by_funder_doi`) and the `dumps` helper for the Zenodo data dumps
  (`list`, `latest`, `download`).
- `RoriferClient.heartbeat()` for the health check of the API.
- Generated sync twin: `RoriferSyncClient`, `OrganizationsSyncClient`,
  `DumpsSyncClient`.
- Pydantic models for organizations, affiliation matches, and dumps.
- `iter_dump_records()` and `index_external_ids()` to read a downloaded dump
  without loading it whole.
- `fundref_id_from_doi()` and `fundref_doi_from_id()` for the Crossref Funder
  Registry crosswalk.

### Changed

- The default pace is 6 requests per second (ROR documents a limit of 2,000
  requests per 5 minutes). Requests to Zenodo run in their own rate class at
  0.5 requests per second, because the anonymous Zenodo search accepts 30
  requests per minute.
- `dumps.list()` sends `all_versions=true`, so every ROR release is one
  record, and follows pages of 25 records. `dumps.latest()` reads the Zenodo
  concept record, which redirects to the newest release.
- `search()`, `iterate()`, `collect()`, and `first()` raise
  `ConfigurationError` for `page_size=`, because ROR fixes pages at 20
  records. `iterate()` raises `ConfigurationError` when a query needs page
  501 instead of stopping without a signal.
- `get()` and `exists()` also accept ids in the form `ror.org/<id>`.
- A response body without an `items` list or without the shape of a record
  raises `APIError`.
