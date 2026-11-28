# Changelog

All notable changes to dataphora are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial client for the DataCite REST API: `DataphoraClient` with the
  `dois` resource (get, exists, search, iterate, collect, first, count,
  per-DOI activities), `activities`, `clients`, `client_prefixes`,
  `providers`, `provider_prefixes`, `repositories`, `prefixes`, and
  `events` resources, plus `totals()` statistics helpers on clients,
  providers, and prefixes.
- `graphql` resource (`client.graphql.query()`) for the public GraphQL
  API: one `POST /graphql` per query, the `data` object back as plain
  dictionaries, and `APIError` with the `errors` list attached.
- Generated sync twin: `DataphoraSyncClient` and one `*SyncClient`
  class per resource.
- Pydantic models for DOI records, client accounts, providers,
  repositories, prefixes, prefix assignments, events, and activities.
  Every model flattens the JSON:API envelope and keeps unknown fields.
- Filter models for the `/dois`, `/clients`, `/providers`,
  `/repositories`, `/prefixes`, and `/events` routes, dumped to the
  upstream hyphenated parameter names.
