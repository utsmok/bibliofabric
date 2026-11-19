# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 0.3.0

Overhaul onto bibliofabric 0.6; see migration notes.

## [0.2.1] - 2026-10

### Fixed

- Crossref field parsing; aligned resource overrides with bibliofabric.

## [0.2.0] - 2026-09

### Added

- Crossref client, models, and resource clients on bibliofabric.
- Cursor/on_error/failures/on_page passthrough for `iterate`.
- Mocked test suite with pytest-httpx integration and live-api smoke tests.
- MkDocs documentation site and README.
- PyPI publishing via trusted publishing on release tags.

### Fixed

- Archive field parsed as a list of strings; prefix/member id URIs normalized.

### Changed

- Pinned dev `ty` and `ruff` versions; updated bibliofabric lock.

## [0.1.0] - 2026-08

### Added

- Project scaffold (uv, ruff, ty, CI).
