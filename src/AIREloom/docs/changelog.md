# Changelog

All notable changes to AIREloom will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- (Details of changes for the next release will go here)

### Changed
-

### Deprecated
-

### Removed
-

### Fixed
-

### Security
-

## [0.1.0] - YYYY-MM-DD (Replace with actual release date)

### Added
- Initial release of AIREloom.
- Asynchronous client for OpenAIRE Graph API (Research Products, Projects, Organizations, Data Sources) and Scholexplorer API.
- Support for NoAuth, Static API Token, and OAuth2 Client Credentials authentication.
- Pydantic models for response validation and data handling.
- Methods for fetching single entities (`get`), searching with pagination/filters/sorting (`search`), and iterating through all results (`iterate`).
- Configurable settings via environment variables, `.env` files, or `ApiSettings` object.
- Built-in retry logic for transient errors and rate limits.
- Optional client-side caching for GET requests.
- Basic request hook system (pre-request and post-request).
- Comprehensive documentation structure.
- Ruff for linting and formatting.
- Pytest for testing.
- `uv` for environment and dependency management.
