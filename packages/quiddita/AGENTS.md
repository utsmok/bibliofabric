# quiddita: Project Guide

quiddita is a placeholder name. Rename the distribution name, the import name, the environment prefix (`QUIDDITA_`), the class prefix (`Quiddita`), and the directories `packages/quiddita`, `src/quiddita`, and `docs/quiddita` together.

quiddita is an async + generated-sync Python client for Wikidata's read interfaces, built on bibliofabric 0.8. Not yet published.

## Architecture

One generic framework layer (bibliofabric) plus a Wikidata-specific overlay. Async I/O modules under `_async/` are the single source of truth; `scripts/unasync.py --package quiddita` generates the `_sync/` twins:

```
QuidditaClient / QuidditaSyncClient   # _async/client.py -> _sync/client.py
 ├─ entities, search                         # ResourceClient subclasses (Action API)
 ├─ claims, sitelinks                        # Action API helpers (plain clients)
 ├─ items, properties, statements            # Wikibase REST API (plain clients)
 ├─ entity_data, lexemes, utilities          # EntityData, lexeme REST, Action modules
 └─ sparql                                   # SparqlClient over QuidditaQueryClient
```

| File(s) | Role |
|---|---|
| `_async/client.py` | `QuidditaClient(BaseApiClient)` on `https://www.wikidata.org` (one host for `w/api.php` and `w/rest.php/wikibase/v1`), and `QuidditaQueryClient(BaseApiClient)` on `https://query.wikidata.org`. The query client receives the main client's settings and limiter instance, so the two hosts share one pace through rate classes (`default`, `sparql`). `aclose()` closes both HTTP clients. |
| `_async/base.py` | `WikidataResourceClient[E]`: `WIKIDATA_DIALECT` and id normalization via `normalize_wikidata_id`; `join_values()` pipes sequences for MediaWiki multi-value parameters. |
| `_async/entities.py` | `EntitiesClient` (`wbgetentities`): `get()` with `select=` (`props`), `params` extras (`languages`, `sitefilter`, `redirects`), chunked `batch_get()` at 50 ids, ordered `iterate_ids()`. |
| `_async/search.py` | `SearchClient` (`wbsearchentities`): `search()` with `language`, `uselang`, `type`, `strict_language`; `count()` raises (no total); REST `search_items()` and `search_properties()`. |
| `_async/claims.py` | `ClaimsClient` (`wbgetclaims`): rank validated client-side (`deprecated`, `normal`, `preferred`). |
| `_async/sitelinks.py` | `SitelinksClient`: `wbgetentities` with `props=sitelinks[/urls]` and `sitefilter`. |
| `_async/rest_items.py` | `ItemsClient` (REST item GET, labels/descriptions with and without fallback, per-site sitelink) and `PropertiesClient` (property GET, `property-data-types`). |
| `_async/statements.py` | `StatementsClient`: REST statements for items and properties (optionally filtered by `property`), and one statement by id (`$` URL-encoded). |
| `_async/entity_data.py` | `EntityDataClient`: `Special:EntityData/{id}.{format}` (`json` parsed to `Entity`, RDF formats as text documents, `revision=`), and `negotiate()` through `/entity/{id}` (303). |
| `_async/lexemes.py` | `LexemesClient`: the WikibaseLexeme REST lexeme route (`wikibaselexeme/v0`); forms and senses come inside the payload, per-form/sense routes do not exist. |
| `_async/utilities.py` | `UtilitiesClient` for `wbavailablebadges`, `wbformatentities`, `wbformatvalue`, `wbparsevalue`, `wbsgetsuggestions` (requires `entity` or `properties`), and `wbcheckconstraints` (entity parameter is `id`). |
| `_async/sparql.py` | `SparqlClient`: `query()` (GET, typed `SparqlResult`), `query_post()` (read-only POST with `retry=True`), `query_text()` (raw body in any format). |
| `dialect.py` | Paths (`ACTION_PATH`, `REST_PREFIX`, `SPARQL_*`), limits (`MAX_IDS_PER_REQUEST` 50, `MAX_SEARCH_LIMIT` 50), `WIKIDATA_DIALECT` (`limit` page size, `continue` offset paging, `search` query, no page numbers, no cursor, no sort, no select). |
| `ids.py` | `normalize_wikidata_id()`: bare `Q`/`P`/`L` id from ids, wiki URLs, and entity URLs; rejects `M` (MediaInfo) and junk. |
| `unwrapper.py` | `QuidditaUnwrapper`: raises on the HTTP 200 `{"error": {...}}` envelope (`no-such-entity` to `NotFoundError`), reads `search` records and single entities. |
| `config.py` | `QuidditaSettings(BaseApiSettings)`, env prefix `QUIDDITA_`, `get_settings()` cached. Defaults: 2 requests per second, concurrency 1, `rate_limits={"sparql": 0.5}`. |
| `models/` | Pydantic v2 models (`Entity`, `Claim`, `Snak`, REST models, `SparqlResult`), `extra="allow"`. |

## Conventions

- Two hosts: `www.wikidata.org` (Action API + REST) and `query.wikidata.org` (SPARQL). No authentication.
- Action API errors answer HTTP 200 with `{"error": {code, info}}`; the unwrapper raises before validation.
- `wbgetentities` answers `toomanyvalues` above 50 ids; every batch path chunks at 50.
- `wbsearchentities` reports no total; `count()` raises `ConfigurationError`.
- `redirects` accepts `yes`/`no`; `wbgetclaims` rank accepts `deprecated`/`normal`/`preferred` only.
- REST payload shape differs from the Action API (string label maps, `{type, content}` values, list qualifiers). `_fields` is documented but rejected by the live API.
- SPARQL POST is read-only and carries `retry=True`.
- No sessions, no loguru: stdlib logging throughout.

## Development

Commands live at the workspace root (see the root `AGENTS.md`). Package-specific bits: regenerate sync twins with `uv run python scripts/unasync.py --package quiddita`, run the suite with `uv run pytest packages/quiddita/tests`, and run the live tests with `uv run pytest -m live_api packages/quiddita/tests` (no credentials needed; keep it to the smoke set, paced at the settings' defaults).

## Testing

`tests/_async/` is the source of truth (sync twin generated in `tests/_sync/`, plus hand-written `tests/test_sync_in_event_loop.py`). Tests without I/O live directly under `tests/` (`test_settings.py`, `test_ids.py`, `test_unwrapper.py`). Tests use pytest-httpx: responses are registered with `add_response(json=...)` without URLs, and the outgoing shape is asserted through `httpx_mock.get_requests()`. Real payload fixtures live in `tests/fixtures/` (trimmed from live responses of 2026-11-27). `tests/_async/test_live_api.py` (and `_sync`) carries the `live_api` marker; the live set is a smoke set of small requests.

## Known gaps

- Write modules of the Action API (`wbeditentity`, `wbsetlabel`, `wbsetclaim`, and the rest) are out of scope: no account credentials exist to test them.
- SPARQL UPDATE is out of scope (the service is read-only for this client).