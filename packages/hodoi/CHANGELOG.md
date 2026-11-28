# Changelog

All notable changes to hodoi are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial client for the DOI System proxy at doi.org: `HodoiClient` with
  `agencies()` (registration agency lookup, in requests of at most 100
  DOIs), `handle()` (typed Handle.net records), `landing_url()`,
  `content()` (negotiated metadata with typed JSON models), and `raw()`
  (un-parsed bytes).
- `resolve()`, which returns the proxy's 302 answer to
  `GET https://doi.org/{doi}` with the landing page URL in the `Location`
  header.
- `locations()`, which reads the proxy's `?action=showurls` listing into
  `RedirectLocation` models, and `parse_locations()` for the XML.
- The `cert` filter of `handle()`, and lists for its `index` and `type`
  filters, sent as repeated query parameters.
- `doi_path()` (percent-encoding for the URL path), `ra_chunks()`, and
  `RA_MAX_PATH_CHARS`.
- Media type catalog in `hodoi.media_types` with the Crossref, DataCite,
  and mEDRA support matrix.
- Pydantic models for the `/ra/` answers, Handle records, and the CSL JSON,
  DataCite JSON, and schema.org JSON-LD representations.
- Generated sync twin: `HodoiSyncClient`.
- DOIs are percent-encoded before they enter the URL path. A DOI inside a
  URL form is decoded first, and its query string or fragment is cut, as in
  `https://doi.org/10.1038/nature12373?from=mail`.
- `/ra/` lookups split long DOI lists so that no request path passes 4000
  characters.
- Every entry of a `/ra/` answer is validated. A body that is not a list
  raises `ConfigurationError`, and a malformed entry raises
  `ValidationError`.
- `content()` returns `None` for an HTTP 204 answer and accepts a media
  type with parameters, such as `application/vnd.citationstyles.csl+json;
  charset=utf-8`.
- `AGENCY_SUPPORT` matches the live answers of 2026-11-28: RIS for mEDRA,
  and no RDF XML or Turtle for DataCite.
