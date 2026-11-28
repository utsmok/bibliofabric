# Changelog

All notable changes to archeion are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `ArcheionClient` and the generated `ArcheionSyncClient` for the arXiv API
  (`https://export.arxiv.org/api`), with no credentials required and the
  pace of the arXiv terms of use (one request every three seconds, one
  connection).
- `client.query` for `/api/query`: `search()` with `search_query`,
  `id_list`, `sortBy`, `sortOrder`, `start`, and `max_results`;
  `iterate()` up to the documented reach of 30,000 results; `get()` and
  `batch_get()` by arXiv id; and `count()`.
- `parse_feed()`, which turns the Atom feed into plain dicts and raises
  `ConfigurationError` for the API's error feeds.
- Pydantic models `ArxivEntry`, `ArxivAuthor`, and `ArxivLink`, with the
  properties `arxiv_id`, `versioned_id`, `version`, `pdf_url`, and
  `author_names`.
