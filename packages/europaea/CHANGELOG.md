# Changelog

All notable changes to europaea are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial client for the Europe PMC REST web services: `EuropaeaClient`
  with the `search` resource (query, cursor paging, sort, synonym, result
  types, index terms), the `articles` resource (records, JATS full text,
  book XML, supplementary files, references, citations, database links, data
  links, labs links, evaluations), the `annotations` resource (by article
  ids, entity, provider, relationship, section and type), the `grants`
  resource (Grist API), the `profiles` resource (`/profile`, `/fields`), and
  the `preprints` resource (search scoped to `SRC:PPR`).
- Generated sync twin: `EuropaeaSyncClient` with the same resources.
- `SearchClient.search_post()` and `SearchClient.iterate_post()` for the
  `POST /searchPOST` route (form-encoded body, cursor paging) and
  `ArticlesClient.status_updates()` for the `POST /status-update-search`
  article status monitor, with typed `StatusUpdateResponse` models.
- Pydantic models for search results, article records, references and
  citations, database and data links, annotations, grant records, and
  profile counts.
