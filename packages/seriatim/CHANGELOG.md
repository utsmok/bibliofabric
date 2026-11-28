# Changelog

All notable changes to this project are documented in this file. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- `SeriatimClient` and the generated `SeriatimSyncClient` for the ISSN Portal.
- `records` resource for the `/resource/ISSN/{issn}` JSON-LD route with
  `get`, `raw` and `exists`, plus `issn_l` for `/resource/ISSN-L/{issn}`.
- `search` resource that reads the Portal's HTML result page with typed
  hits, paging, `count`, and a page iterator.
- `ltwa` resource that reads the Title Word Abbreviation table with typed
  rows, paging, and an iterator over the whole table.
- `issn_l.download_table()` and the readers `iter_issn_to_issn_l()` and
  `iter_issn_l_clusters()` for the public ISSN-L table zip, which maps every
  assigned ISSN to its ISSN-L.
- Typed models for record nodes, search hits, and LTWA rows; every model
  keeps unknown keys and record models keep the raw JSON-LD node.
- ISSN validation and normalization helpers on top of `bibliofabric.ids`.
