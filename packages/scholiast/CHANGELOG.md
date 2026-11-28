# Changelog

All notable changes to scholiast are documented here. The format
is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial client for the Semantic Scholar APIs: `ScholiastClient`
  with the `papers` resource (get by every id form, `search`,
  `bulk_search`, `bulk_iterate`, `batch`, `citations`, `references`,
  `authors`, `autocomplete`, `search_match`), the `authors` resource
  (`get`, `search`, `papers`, `batch`), `recommendations` (`for_paper`,
  `for_list`), `datasets` (`releases`, `release`, `latest`, `dataset`,
  `diffs`), `snippets` (`search`), and `patents` (`get`, `search`,
  `outbound_citations`).
- Generated sync twin: `ScholiastSyncClient` with the same
  resource clients.
- Pydantic models for papers, authors, citations, references, embeddings,
  tldrs, snippets, patents, recommendations, and dataset releases, with
  `extra="allow"` so new upstream fields survive.
- Optional API key support: `SCHOLIAST_API_KEY` travels as the
  `x-api-key` header; keyless callers use the shared anonymous pool.
- Default pacing of 1 request per second with concurrency 1, matching the
  published per-key limit and the contended anonymous pool.
- Every route percent-encodes the paper, author, or patent id as one path
  segment, so all id forms (including `URL:` ids) work on the sub-list
  routes too. A blank id raises `ConfigurationError`.
- A rejected API key (HTTP 403) raises `AuthError` without the key in the
  message.
