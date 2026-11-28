# Changelog

All notable changes to orchis are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `OrchisClient` and the generated `OrchisSyncClient` for the ORCID
  Public API v3.0 (`https://pub.orcid.org/v3.0`), with resource clients for
  the record summary, the person section and its sub-sections, the
  activities summary and its sections, the single-item routes, and the two
  search routes (`expanded-search` and the Solr-compatible `search`).
- Pydantic models for records, person sections, activity sections, works,
  funding, peer reviews, and search results, all with `extra="allow"`.
- `text()` accessor and `.text` properties that unwrap ORCID's
  `{"value": ...}` wrappers.
- `representation()` methods that return the XML body of record and activity
  routes as text.
- Optional `ORCHIS_ACCESS_TOKEN` setting, sent as a bearer header to lift
  the public API daily read quota.
