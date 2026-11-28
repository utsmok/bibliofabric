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

### Fixed

- DOIs are percent-encoded before they enter the URL path, and a DOI
  inside a URL form is decoded first.
- A query string or fragment in a DOI URL is cut before the lookup, as in
  `https://doi.org/10.1038/nature12373?from=mail`.
- A list of long DOIs no longer produces one overlong `/ra/` path. A
  request also ends when its path would pass 4000 characters.
- Every entry of a `/ra/` answer is validated. A body that is not a list
  raises `ConfigurationError`, and a malformed entry raises
  `ValidationError` instead of passing through.
- `content()` returns `None` for an HTTP 204 answer and accepts a media
  type with parameters, such as `application/vnd.citationstyles.csl+json;
  charset=utf-8`.
- `AGENCY_SUPPORT` lists RIS for mEDRA and no longer lists DataCite for
  RDF XML and Turtle, matching the live answers of 2026-11-28.
