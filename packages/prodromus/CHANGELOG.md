# Changelog

All notable changes to prodromus are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `ProdromusClient` and the generated `ProdromusSyncClient` for the bioRxiv
  and medRxiv API (`https://api.biorxiv.org`), with no credentials required.
- `details`: `get()` (every version of a DOI), `search()` and `iterate()`
  over a date range with an optional subject category, and `recent()` for
  the newest posts by count or by days.
- `published`: `get()` by preprint or journal DOI, `search()` and
  `iterate()` over a date range, `by_publisher()` and
  `iterate_by_publisher()` for a publisher DOI prefix, and `biorxiv()` for
  the `pub` route.
- `funders`: `search()` and `iterate()` over the preprints that declare a
  funder ROR id.
- `statistics`: `content()` and `usage()` per month or year.
- Pydantic models `Preprint`, `FunderDeclaration`, `PublishedArticle`,
  `ContentStatistic`, and `UsageStatistic`; error statuses that the API
  answers with HTTP 200 raise `ConfigurationError`.
