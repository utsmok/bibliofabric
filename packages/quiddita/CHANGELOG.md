# Changelog

All notable changes to quiddita are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial client for Wikidata's read interfaces:
  `QuidditaClient` with the `entities` (`get`, `batch_get`,
  `iterate_ids`), `search` (`search`, `iterate`, `collect`, `first`,
  `search_items`, `search_properties`), `claims`, `sitelinks`, `items`,
  `properties`, and `statements` resources.
- `QuidditaQueryClient` for the SPARQL query service on
  `query.wikidata.org`, exposed through `client.sparql` (`query`,
  `query_post`, `query_text`); it shares the settings object and the rate
  limiter with the main client.
- Generated sync twin: `QuidditaSyncClient` and the sync resource twins.
- Pydantic models for Action API entities, claims, snaks, REST items,
  properties, statements, search hits, and SPARQL 1.1 JSON results.
- `normalize_wikidata_id()` for id and URL normalization.
- `client.entity_data` for `Special:EntityData`: `get()` parses the `json`
  format into `Entity` and returns the RDF formats as typed text documents;
  `revision=` serves old revisions; `negotiate()` follows the
  `/entity/{id}` content-negotiation redirect.
- `client.search.suggest_items()` and `suggest_properties()` for the REST
  suggest routes.
- `client.lexemes` for the WikibaseLexeme REST lexeme route (lemmas, forms,
  senses).
- `client.utilities` for the Action read modules `wbavailablebadges`,
  `wbformatentities`, `wbformatvalue`, `wbparsevalue`, `wbsgetsuggestions`,
  and `wbcheckconstraints`.
