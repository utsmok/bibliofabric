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
- `person.other_names()` and `person.item()` for the other names and for
  single person items by put code, `activities.works_bulk()` for up to 100
  full works per request, and `expanded_search.csv()` for the CSV search
  route (`/csv-search`).
- Pydantic models for records, person sections, activity sections, works,
  funding, peer reviews, and search results, all with `extra="allow"`.
  They validated 300 section reads and 890 full works of 60 live records
  on 2026-11-28; identifier lists may be `null` and identifier
  normalization errors are objects (`NormalizationError`).
- `text()` accessor and `.text` properties that unwrap ORCID's
  `{"value": ...}` wrappers.
- `representation()` methods that return the XML body of record and activity
  routes as text.
- Optional credentials that lift the public API daily read quota:
  `ORCHIS_ACCESS_TOKEN` is sent as a bearer header, and without it
  `ORCHIS_CLIENT_ID` with `ORCHIS_CLIENT_SECRET` mint a `/read-public` token
  on the first request (client-credentials grant). Setting only one of the
  pair raises `ConfigurationError`.
