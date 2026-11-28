# Changelog

All notable changes to AIREloom are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/); versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.1] - 2026-11-28

### Changed

- Requires `bibliofabric>=0.8,<0.9`; `request()` forwards the new
  `follow_redirects=` argument.

## [0.9.0] - 2026-11-27

### Breaking

- **Scholix date filters fail fast:** Passing `from_date` or `to_date` (or raw
  `"from"` / `"to"` keys in dict filters) to `client.scholix.search_links`,
  `iterate_links`, `search_links_v2`, or `iterate_links_v2` now raises
  `ConfigurationError` instead of routing to V2 with a warning, preventing
  silent zero-row results on V3 and silent unfiltered results on V2. Filter by
  `link_publication_date` client-side or query Graph V4 research products with
  `from_publication_date` / `to_publication_date`.
- **Partial OAuth2 credentials rejected:** Setting only one of
  `openaire_client_id` or `openaire_client_secret` (without `refresh_token` or
  explicit `auth_strategy`) now raises `ConfigurationError` instead of silently
  falling back to `NoAuth()`.

### Added

- **`RefreshTokenAuth` support:** Added `openaire_refresh_token`
  (`AIRELOOM_OPENAIRE_REFRESH_TOKEN`, `repr=False`) on `AireloomSettings` and
  `refresh_token=` on `AireloomClient` / `AireloomSyncClient`, wiring up
  `bibliofabric.RefreshTokenAuth` when set.
- **`auth_strategy=` constructor kwarg:** Added keyword-only `auth_strategy=` to
  `AireloomClient.__init__` / `AireloomSyncClient.__init__` matching sibling
  clients; `auth=` remains as a deprecated alias (emitting `DeprecationWarning`)
  and passing both raises `ConfigurationError`.
- **Client kwargs & error-collection alignment:** Added `http_client=`,
  `mailto=`, `client_id=`, and `client_secret=` constructor kwargs on
  `AireloomClient` / `AireloomSyncClient`, and aligned `on_error` / `failures`
  forwarding across Graph and Scholix resources.
- **`retry=` forwarding:** `AireloomClient.request()` /
  `AireloomSyncClient.request()` now accept and forward `retry: bool | None = None`
  to match `BaseApiClient.request()`.
- **Python 3.14:** Added `"Programming Language :: Python :: 3.14"` classifier.

### Changed

- **Core dependency:** Updated `bibliofabric` dependency to `>=0.7,<0.8`.
- **Relaxed undocumented response `Literal`s:** Relaxed `RefereedType`
  (`Instance.refereed`, `RelatedInstance.refereed`) and
  `CitationImpact.*Class` (`influenceClass`, `citationClass`,
  `popularityClass`, `impulseClass`) to `str | None` while documenting known
  values in docstrings.
- **Core offset guard:** Moved the Graph V4 `10_000` offset cap to
  `GRAPH_DIALECT.max_offset` so `GraphResource` reuses core's offset guard.

### Fixed

- **Graph V4 pagination & limits:** Set `GRAPH_DIALECT.max_page_size = 100`,
  fixed `ResearchProductsResource.by_orcid()` to paginate up to `limit`,
  enforced OpenAIRE's 50-value OR filter cap client-side, and bounded
  concurrency in `ResearchProductsResource.get_fields()`.
- **Filter serialization:** Fixed empty `GraphFilters` serialization and
  list-valued filter handling (skipping `None` and empty collections, proper OR
  grouping and value quoting).
- **Scholix & validation:** Fixed Scholix `linkProvider` V2 routing and wrapped
  custom model validation through `bibliofabric.validate_model` and `parse_json`
  so schema errors consistently raise `bibliofabric.ValidationError`.
- **Models & unwrapper:** Fixed `Project.parse_keywords_string` to split
  semicolon-separated keywords, fixed nullable/computed fields across Graph and
  Scholix models, and fixed `OpenAireUnwrapper` edge cases for metadata, totals,
  and single-item payloads.
- **Safe client teardown:** Wrapped Graph and Scholix client shutdown in
  `aclose()` / `close()` with `try`/`finally` so an error closing one client
  never leaks the other.

## [0.8.0] - 2026-11-26

### Breaking

Overhaul onto the rewritten bibliofabric 0.6 core, and migration of all Graph
API list operations to the V4 filter-based queries (D-14).

- `AireloomClient` replaces `AireloomSession`; there is no `Session` class and
  no `session.queries` accessor. Helper queries became typed resource methods
  with bounded defaults.
- `search()` returns `bibliofabric.Page[E]` (`results`, `total`, `next_cursor`,
  `page`, `meta`) instead of the aireloom response envelopes. The envelope
  models (`ApiResponse`, `Header`, `*Response`, `LinksResponse`,
  `ScholixResponse`) are deleted.
- List operations hit `https://api.openaire.eu/graph/v4/{research-products,
  projects,organizations,datasources,persons}` with the single `filter=`
  expression; `get(id)` keeps the V3 by-id route because V4 has none.
- Filter models moved from `aireloom.endpoints` to `aireloom.filters` and use
  V4 field names (snake_case, dotted names as pydantic aliases). See the
  migration table below.
- Sorting is `sort="field:dir"` with snake_case fields (e.g.
  `citation_count:desc`); invalid fields raise `ConfigurationError` instead of
  an HTTP 400.
- Scholix V1 endpoints (`links_from_pid`, `links_from_publisher`,
  `links_from_datasource`, `list_datasources`, `ScholixV1Link`) are removed.
  V3 is the default; `search_links_v2` / `iterate_links_v2` stay available and
  date-filtered queries (`from_date`/`to_date`) are routed to V2 automatically
  because V3 returns zero rows for them. Link methods return typed
  `ScholixRelationship` records (`Page[ScholixRelationship]`).
- Relations helpers return typed records: `get_relations_info()` returns
  `list[RelationInfo]`, `iterate_links()` yields `Relation`.
- Authentication is client credentials (Keycloak token endpoint) or anonymous;
  the static-token setting (`AIRELOOM_OPENAIRE_API_TOKEN`), the
  `new_token_endpoint` toggle, and `effective_token_url` are removed. Pass an
  explicit `auth=StaticTokenAuth(...)` if you need a bearer token.
- `client.scholix` runs on a dedicated internal client for the Scholexplorer
  host (1 req/s limiter); Graph requests default to 2 req/s with concurrency 4.
- Deleted modules: `session.py`, `queries.py`, `endpoints.py`, `constants.py`,
  `resources/_batch.py`, `resources/_standard.py`. Logging is standard-library
  `logging` (no loguru, no import-time configuration).
- `iterate_links` / Scholix iteration stop on empty pages or the reported
  total; both routes remain page-based without a cursor, so page windows can
  shift between requests (upstream limitation, documented).

### Added

- Sync support: `AireloomSyncClient` and the `Sync*` resource classes
  (`SyncResearchProductsResource`, `SyncScholixResource`, and so on),
  generated from the async sources with `scripts/unasync.py`. The sync client
  uses `httpx.Client`, `time.sleep`, and threads; it never starts or touches
  an event loop, so it works in scripts, notebooks, and inside a running
  event loop. I/O modules now live in `aireloom._async` and `aireloom._sync`;
  every public name stays importable from the package root.

- `client.persons.batch_get_by_orcid(orcids)`: fetches person records for many
  ORCID iDs with one `ids.original:a|b|c` request per 50 iDs (verified live on
  2026-11-26), keyed by the hyphenated ORCID. Closes the batch-getter half of
  issue #1.

- Typed relation vocabulary from the links relations-info payload:
  `RelationName`, `RELATION_INVERSES`, and `relation_inverse(name)`
  (`Cites` -> `IsCitedBy`), exported from the package root.
- `client.research_products.by_orcid(orcid, *, limit=100)` — normalizes the
  ORCID and filters on the V4 `authorships.author.orcid` field.
- `client.organizations.find_variants(names, *, country=None)` — one search
  per name fragment, deduplicated by id, keeping `pending_org_::` records
  because they carry org-project links the canonical records dropped.
- `client.research_products.get_fields(ids, fields)` — sparse batch fetch in
  one request via the V4 `select` parameter plus an `id` OR-filter
  (verified live).

### Migration from 0.7

| 0.7 call | 0.8 call |
|---|---|
| `AireloomSession()` | `AireloomClient()` |
| `session.research_products.search(filters, sortBy="publicationDate desc")` | `client.research_products.search(filters, sort="publication_date:desc")` |
| `session.research_products.iterate(filters, page_size=50)` | `client.research_products.iterate(filters, page_size=100)` |
| `session.queries.publications_by_doi(*dois)` | `client.research_products.batch_get_by_doi(dois)` |
| `session.queries.citing_works(doi)` | `client.scholix.search_links(ScholixFilters(sourcePid=doi, relation="References"))` |
| `session.scholix.search_links(...)` → `ScholixResponse` | `client.scholix.search_links(...)` → `Page[ScholixRelationship]` |
| `response.results[i].title` | `page.results[i].mainTitle` |
| `LinksFilters` import from `aireloom.endpoints` | from `aireloom.filters` |
| `AIRELOOM_OPENAIRE_API_TOKEN=...` | `auth=StaticTokenAuth(token=...)` |
| `AIRELOOM_NEW_TOKEN_ENDPOINT=1` | default behavior (Keycloak endpoint) |

### V3 filter name → V4 filter field

| V3 parameter (0.7 model field) | V4 filter field (0.8 model field) |
|---|---|
| `type` | `type` |
| `mainTitle` | `title.search` (`title_search`) |
| `id` / `pid` / `originalId` | `id` / `ids.pid` / `ids.original` (plus `ids.doi`, `ids.pmid`, ...) |
| `fromPublicationDate` / `toPublicationDate` | `from_publication_date` / `to_publication_date` |
| `fromPublicationYear` / `toPublicationYear` | `from_publication_year` / `to_publication_year` |
| `countryCode` | `authorships.countries` (`authorships_countries`) |
| `authorFullName` / `authorId` | `authorships.author.fullname` / `authorships.author.orcid` |
| `accessRightLabel` | `best_oa.rights` (`best_oa_rights`) |
| `openAccessColor` | `oa_color` |
| `isGreen` / `isPeerReviewed` / `isInDiamondJournal` / `isPubliclyFunded` | `is_green` / `is_peer_reviewed` / `is_in_diamond_journal` / `is_publicly_funded` |
| `influenceClass` / `popularityClass` / `impulseClass` / `citationCountClass` | `impact.influence_class` / `impact.popularity_class` / `impact.impulse_class` / `impact.citation_count_class` |
| `instanceType` | `instance_type` |
| `sdgLabel` / `fos` | `sdg` / `fos` |
| `subjects` / `language` / `publisher` | `subjects` / `language` / `publisher` |
| `relProjectId` / `relProjectCode` | `grants.project_id` / `grants.code` |
| `relProjectFundingShortName` / `relProjectFundingStreamId` | `grants.funder_short_name` / `grants.funding_stream_id` |
| `hasProjectRel` | `has_grant` |
| `relOrganizationId` | `affiliations.organization_id` |
| `relCommunityId` | `communities.id` |
| `relHostingDataSourceId` / `relCollectedFromDatasourceId` | `host_datasource.id` / `collected_from.id` |
| `rorId`, `relOrganization`, `relCommunityName`, `subCommunity`, `relFunder`, `excludePubDateRange`, `logicalOperator`, `source` | no V4 equivalent (dropped) |
| Projects: `fundingShortName` / `fundingStreamId` / `fundinglevel0Id` | `funder_short_name` / `funding_stream_id` / `funding_level_0_id` |
| Projects: `projectStatus` (0.8 adds) | `project_status` (`completed\|ongoing\|planned`) |
| Projects: `fromStartDate` etc. | `from_start_date` / `to_start_date` / ... |
| Projects: `relOrganizationId` / `relOrganizationName` | `organizations.id` / `organizations.name` |
| Organizations: `legalName` / `legalShortName` | `legal_name.search` / `legal_short_name.search` |
| Organizations/DS/Projects: `countryCode` / `country` | `country` (+ new `continent`) |
| Data sources: `dataSourceTypeName` / `eoscdatasourcetype` | `type` / `eosc_datasource_type` |
| Data sources: `compatibilityId` / `compatibilityName` | `compatibility.id` / `compatibility.name` |
| Persons: `originalId` / `givenName` / `lastName` | `ids.original` / `given_name` / `last_name` |

### Added

- Typed `facets(*fields)` and `group_by(field)` helpers on every entity
  resource, returning counts (`dict[str, dict[str, int]]` / `dict[str, int]`).
- `select=` sparse fieldsets and the top-level `query=` full-text search on
  every `search()` call.
- Cursor-resumable iteration: `iterate(..., on_page=...)` reports
  `next_cursor`, and `iterate(..., cursor=saved)` resumes a harvest.

## [0.7.0] - 2026-11-02

### Changed

- The default token endpoint is now the OpenAIRE Keycloak URL; the legacy
  `aai.openaire.eu/oidc/token` endpoint was retired on 2026-11-02 and returns
  410 Gone. `AIRELOOM_NEW_TOKEN_ENDPOINT=0` falls back to the retired legacy
  URL.

## [0.6.0] - 2026-10-27

### Added

- Opt-in toggle for the new OpenAIRE token endpoint
  (`AIRELOOM_NEW_TOKEN_ENDPOINT=1` switches the client-credentials token
  request to the post-2026-11-02 Keycloak endpoint; off by default). An
  explicit `AIRELOOM_OPENAIRE_TOKEN_URL` still wins.

### Fixed

- Invalid-mutable-override diagnostics from newer `ty`: base class
  annotations matched for `_entity_model`/`_search_response_model`, and the
  two intentional schema-field shadowing overrides are suppressed.


## [0.5.2] - 2026-09-08

Scholix compatibility and metadata fidelity release.

### Added

- Scholix V1 and V2 endpoint helpers for link providers, publisher directories,
  data sources, links, and KPI data.
- V2 Scholix filters for link providers and source/target PID types.

### Fixed

- Research product keywords and descriptions now preserve the API's structured
  values.
- Scholix `subType` and identifier fields accept the casing used by both API
  generations.
- Person batch lookups support both `id` and `originalId` identifiers.

## [0.5.1] - 2026-09-05

Dependency alignment release; no API changes.

### Changed

- Widened the `bibliofabric` dependency to `>=0.5.1,<0.6.0`, picking up
  bibliofabric 0.5.x: pluggable paging strategies (`page`/`offset` with
  None-able parameter names), resumable cursor iteration (`cursor=` +
  `on_page` checkpoints), explicit per-record parse-failure modes
  (`on_error="skip"/"raise"` with a `failures` collector), bounded
  concurrent page fetches (`concurrency=N`), and opt-in proactive rate
  pacing from `X-RateLimit-*` headers (`rate_limit_pacing=True`).
- Verified live against the OpenAIRE Graph v3 API: research-product
  search/get with raw-vs-parsed field comparison, 3-page cursor
  iteration with `on_page` checkpointing and no duplicate ids, and
  project search.

## [0.5.0] - 2026-09-04

Stable promotion of the v3 line: identical feature set and breaking changes as
0.5.0a1 (see [Migration to v3](docs/migration-to-v3.md)), plus the additions below.

### Added

- `ProjectLinkPid` model for PID entries inside V3 `Project.links[]` items
  (`value`/`type`/`typeLabel`)
- `Organization.fundings[].jurisdiction` tolerates `null` payloads (coerced to
  an empty model instead of failing validation)
- Documented live quirks: research-products `pageSize > 100` returns HTTP 400
  in page and cursor modes; unsorted-page ordering/membership instability;
  Scholix requires bare pids

### Changed

- `projects_by_organization(search_on="name")` uses full-text `search` —
  organization names rarely appear in project text fields, so
  `search_on="openaire_id"` is recommended for identifier lookups

## [0.5.0a1] - 2026-07-21

AIREloom now targets the OpenAIRE Graph API **v3** (v1/v2 deprecated by OpenAIRE). This is a **breaking** release; see [Migration to v3](docs/migration-to-v3.md).

### Added

- V3 Graph API support: single base URL `https://api.openaire.eu/graph/v3` for all entities (kebab-case paths)
- 41 new filter parameters across Research Products (+20), Projects (+13), Data Sources (+8)
- `logicalOperator` accepts `AND`/`OR`/`NOT` on all Graph filter models
- Typed response fields: `eoscIfGuidelines`, `publiclyFunded`, `isGreen`, `isInDiamondJournal`, `openAccessRoute`, `conferencePlace`/`conferenceDate`, organizational `fundings`/`collectedFrom`/`originalIds`, project `funding`/`links`, data source `eoscdatasourcetype`/`jurisdiction`/`odlanguages`/`links`, `Subject.provenance`
- Auto-quoting of filter values containing spaces/operators/parentheses (`GraphV3FilterSerializationMixin`)
- `popularity` sort field for Research Products
- Migration guide (`docs/migration-to-v3.md`)

### Changed

- **BREAKING:** filter renames — `authorOrcid`→`authorId`, `bestOpenAccessRightLabel`→`accessRightLabel`, `sdg`→`sdgLabel`
- **BREAKING:** `sdg: list[str]` → `sdgLabel: str` (use inline OR for multiple)
- **BREAKING:** Projects date filters (`fromStartDate`/`toStartDate`/`fromEndDate`/`toEndDate`) are now `str` (accept bare years like `"2022"`)
- **BREAKING:** Links endpoint is 0-indexed (first page `page=0`); page size silently capped at 99 by the server (library clamps + warns)
- Data source `accessRights`/`uploadRights`/`databaseAccessRestriction` relaxed from `Literal` to `str` per v3 spec

### Removed

- **BREAKING:** `grantID` filter (Projects) — dropped by v3
- Persons `startDate`/`endDate` sort fields — rejected by v3 validation
- Per-entity v1/v2 base URL routing (`_base_url_override` on Graph resource clients)

## [0.3.0] - 2025-06-04

### Added

- Ergonomics layer: `SafeList`/`SafeStr` types, computed properties on all models
- Convenience query functions (`search_by_doi`, `search_publications`, etc.)
- Iterator helpers: `collect()`, `count()`, `first()` on all resource clients
- Persons endpoint (OpenAIRE Graph API v1)
- Research Product Links and Relations Info endpoints
- Per-entity API version routing (researchProducts → v2, others → v1)
- Scholix v3 pagination fix
- Marimo notebook examples (dual-purpose scripts + interactive notebooks)

### Changed

- All routine operational logging downgraded from INFO to DEBUG
- CI ruff format check replaced with pre-commit hook
- Examples converted to marimo notebooks

## [0.2.0] - 2025-06-03

### Added

- Initial public release
- Async client for OpenAIRE Graph API and Scholexplorer API
- Support for NoAuth, Static Token, and OAuth2 Client Credentials
- Pydantic models for all response types
- Cursor-based and page-based pagination
- Configurable retry logic and rate limiting
- Optional client-side caching
- Request hook system
