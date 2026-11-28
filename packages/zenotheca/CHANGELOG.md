# Changelog

All notable changes to zenotheca are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Vocabularies resource (`VocabulariesClient`): `search()`, `iterate()`,
  and `get()` for `resourcetypes`, `licenses`, `languages`, and
  `communitytypes`, with the `ZenothecaVocabulary` model.
- OAI-PMH client (`OaiClient`) for `https://zenodo.org/oai2d`:
  `identify()`, `list_metadata_formats()`, `list_sets()`,
  `list_identifiers()`, `list_records()`, `get_record()`, plus
  `iterate_records()` and `iterate_identifiers()` over resumption tokens.
  OAI errors map to bibliofabric exceptions (`noRecordsMatch` answers an
  empty page, `idDoesNotExist` raises `NotFoundError`, bad arguments raise
  `ConfigurationError`).
- `ZenothecaCommunitiesClient.subcommunities()`.
- Optional access token: `ZENOTHECA_API_TOKEN` (hidden from `repr`)
  sends `Authorization: Bearer` and switches to the authenticated dialect
  with a page size cap of 100.
- Pydantic models for vocabulary entries and the OAI-PMH answers
  (`OaiIdentifyResponse`, `OaiFormats`, `OaiSets`, `OaiIdentifiers`,
  `OaiRecords`, `OaiRecordResponse`, `OaiRecord`, `OaiHeader`,
  `OaiResumptionToken`, and friends).
- Initial client for the Zenodo REST API: `ZenothecaClient` with the
  `records` resource (`get`, `exists`, `search`, `iterate`, `count`,
  `versions`, `latest`, `files`, `download_file`) and the `communities`
  resource (`search`, `get`, `iterate`, `records`).
- Generated sync twin: `ZenothecaSyncClient`, `ZenothecaRecordsSyncClient`,
  `ZenothecaCommunitiesSyncClient`.
- Pydantic models for records, record metadata, files, file listings,
  communities, and community metadata.
- Elasticsearch `q` clause builders (`term`, `phrase`, `community`,
  `resource_type`, `any_of`, `all_of`).
- `normalize_record_id()` and `normalize_community_slug()` for the bare id,
  DOI, and URL spellings Zenodo answers.
- The two search routes (the record search and the search over the records
  of one community) run in their own `search` rate class at 0.5 requests
  per second, because they allow 30 requests per minute without a token.
  The overall default is 2 requests per second for the other routes, which
  allow 133 per minute.
