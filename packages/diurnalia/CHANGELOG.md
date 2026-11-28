# Changelog

All notable changes to diurnalia are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `DiurnaliaClient` and the generated `DiurnaliaSyncClient` for the DOAJ API v4 (`https://doaj.org/api/v4`), with no credentials required.
- `journals` and `articles` resources. Each exposes `search()`, `iterate()`, `collect()`, `first()`, and `count()` with the `page`/`pageSize` dialect, `get()` through the search route (`JournalsClient.get(issn)` and `ArticlesClient.get(doi)`), and `get_by_id()` through the record routes (`/api/v4/journals/{id}` and `/api/v4/articles/{id}`).
- `issn_query()` and `doi_query()` helpers that build normalized fielded clauses.
- Pydantic models for journal and article records and every `bibjson` field the API serves (`Journal`, `Article`, and their parts), all open to extra fields.
- `DiurnaliaSettings` with the `DIURNALIA_` prefix; the request pace defaults to 1 per second against the documented limit of 2 per second.
